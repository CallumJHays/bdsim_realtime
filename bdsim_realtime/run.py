
from typing import Callable, Dict, Iterator, List, Optional, Set
import time
import sched

from bdsim import Block, BlockDiagram, BDSimState
from bdsim.components import Clock, ClockedBlock, SinkBlock

from .tuning import Tuner


def _clocked_plans(bd: BlockDiagram) -> Dict[Clock, List[Block]]:
    plans: Dict[Clock, List[Block]] = {}

    prev_clock_period = 0

    # TODO: implement sim mode context manager
    assert not any(b.blockclass == 'transfer' for b in bd.blocklist), \
        "Tranfer blocks are not supported in realtime execution mode (yet). Sorry!"

    bd.reset()

    for clock in sorted(bd.clocklist, key=lambda clock: clock.offset):

        # assert that all clocks' periods are integer multiples of eachother so that they don't overlap.
        # Should really be done at clock definition time.
        # May be avoided with some multiprocess magic - but only on multicore systems.
        assert (prev_clock_period % clock.T == 0) or (
            clock.T % prev_clock_period == 0)
        prev_clock_period = clock.T

        # Need to find all the blocks that require execution on this Clock's tick.
        connected_blocks: Set[Block] = set()

        def should_exec(b: Block) -> bool:
            is_planned = any(
                block
                for plan in plans.values()
                for block in plan
                if block is b
            )
            return not is_planned \
                and (not isinstance(b, ClockedBlock) or b.clock is clock)

        # Recurse backwards and forwards to collect these
        for block in clock.blocklist:
            connected_blocks.update(set(  # Backwards
                _collect_connected(block, forward=False, predicate=should_exec)
            ))
            connected_blocks.update(set( # Forwards
                _collect_connected(block, forward=True, predicate=should_exec)
            ))

        # plan out an order of block .output() execution and propagation. From sources -> sinks
        # collect sources and ClockedBlocks with inputs ready (at this clock tick offset)
        plan = []
        for b in connected_blocks:
            if b.nin == 0 or (isinstance(b, ClockedBlock) and all(b.inputs)):
                plan.append(b)

        # then propagate, updating plan as we go
        idx = 0
        while idx < len(plan):
            block: Block = plan[idx]
            block.output_values = [True] * block.nout

            for outwires in block.output_wires:
                for outwire in outwires:
                    block_next: Block = outwire.end.block

                    if all(inp is not None for inp in block_next.inputs) \
                    and (block_next.clock is clock if isinstance(block_next, ClockedBlock) else True) \
                    and block_next not in plan:
                        plan.append(block_next)
                        # reset output values to prevent this from getting added to plan again
                        block_next.output_values = [None] * block.nout

            idx += 1

        plans[clock] = plan


    set_planned = set(
        plan
        # flatmap clockplan values
        for clockplan in plans.values()
        for plan in clockplan
    )
    not_planned = set(bd.blocklist) - set_planned
    assert not any(not_planned), """Blocks {} do not depend on or are a dependency of any ClockedBlocks.
This is required for its real-time execution.""" \
    .format(not_planned)
    # TODO: bd.simulation_only:
# Mark the blocks as sim_only=True if they are not required for realtime execution, or declare them within the `with bdsim.simulation_only: ...` context manager""" \

    return plans

def run(bd: BlockDiagram, max_time: Optional[float]=None, tuner: Optional[Tuner] = None):
    state = bd.state = BDSimState()
    state.T = max_time

    if not bd.compiled:
        bd.compile()
        print("Compiled!\n")

    clock2plan = _clocked_plans(bd)

    bd.start(state=state)
    
    if tuner:
        # needs to happen after self.start() because the autogen'd block-names
        # are used internally
        tuner.setup()
    
    last_most_frequent_clock = sorted(bd.clocklist, key=lambda c: c.T + c.offset)[0]

    SETUP_WAIT_BUFFER = 1 # in seconds, to give time for the planning and scheduling
    now = time.monotonic()

    # use python's stdlib scheduler
    scheduler = sched.scheduler()

    print("Executing {}:".format(max_time or "forever"))

    for clock, plan in clock2plan.items():
        scheduled_time: float = now + clock.offset + SETUP_WAIT_BUFFER
        print("{} <SCHEDULED for {}>:{}".format(
            clock, scheduled_time,
            ''.join('\n\t{}. {}{}'.format(idx, b, ' (clocked)' if isinstance(b, ClockedBlock) else '') for idx, b in enumerate(plan))))
        scheduler.enterabs(
            scheduled_time,
            priority=1,
            action=exec_plan_scheduled,
            argument=(
                clock,
                plan,
                state,
                scheduler,
                scheduled_time,
                scheduled_time,
                tuner if clock is last_most_frequent_clock else None))

    print("System time (time.monotonic()) is now {}. Running scheduler.run()!".format(time.monotonic()))
    try:
        scheduler.run()
    finally:
        bd.done()
    print("Realtime Execution Stopped AS EXPECTED")


def exec_plan_scheduled(
    clock: Clock,
    plan: List[Block],
    state: BDSimState,
    scheduler: sched.scheduler,
    scheduled_time: float,
    start_time: float,
    tuner_to_update: Optional[Tuner]
):
    state.t = scheduled_time - start_time
    
    # execute the 'ontick' steps for each clock, ie read ADC's output PWM's, send/receive datas
    # for b in clock.blocklist:
    #     # if this block requires inputs, only run .next() the second time this was scheduled.
    #     # this way, its data-dependencies are met before .next() executes
    #     if scheduled_time == start_time and not isinstance(b, SourceBlock):
    #         continue
    #     b._x = b.next()
    
    # now execute the given plan
    for b in plan:
        if isinstance(b, ClockedBlock):
            b._x = b.next()

        if isinstance(b, SinkBlock):
            b.step()  # step sink blocks
        else:
            # propagate all other blocks
            b.output_values = b.output(state.t)

    # forcibly collect garbage to assist in fps constancy
    # gc.collect()

    # print('after collect()', time.monotonic() - scheduled_time)

    if not state.stop and (state.T is None or state.t < state.T):
        next_scheduled_time: float = scheduled_time + clock.T
        scheduler.enterabs(
            next_scheduled_time,
            priority=1,
            action=exec_plan_scheduled,
            argument=(
                clock,
                plan,
                state,
                scheduler,
                next_scheduled_time,
                start_time,
                tuner_to_update))
    
    if tuner_to_update:
        tuner_to_update.update()


def _collect_connected(
    block: Block,
    forward: bool,
    predicate: Callable[[Block], bool]
) -> Set[Block]:
    """Recurses connections in the block diagram, either forward or backward from a given block.
    Collects the blocks into the provided "collected" set.
    if forward=True, will recurse through outputs, otherwise will recurse through inputs
    """

    yield block
    
    wires = block.output_wires if forward else block.input_wires

    for ws in wires:
        for wire in ws:
            next_block = wire.end.block if forward else wire.start.block
            if predicate(next_block):
                yield from _collect_connected(next_block, forward, predicate)
