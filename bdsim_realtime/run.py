
from typing import Callable, Dict, List, Optional, Set
import time
import sched

from bdsim import Block, BlockDiagram, BDSimState
from bdsim.components import Clock, ClockedBlock, SinkBlock

from .tuning import Tuner


def _clocked_plans(bd: BlockDiagram):
    plans: Dict[Clock, List[Block]] = {}

    prev_clock_period = 0
    # track to make sure we're actually executing all blocks on clock cycles properly.
    # otherwise the realtime blockdiagram is not fit for realtime execution
    in_clocked_plan: Dict[Block, bool] = {
        block: False for block in bd.blocklist
    }

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
            return not in_clocked_plan[b] \
                and (not isinstance(b, ClockedBlock) or b.clock is clock)

        # Recurse backwards and forwards to collect these
        for block in clock.blocklist:
            _collect_connected(block, connected_blocks,
                               forward=False, predicate=should_exec)  # Backwards
            _collect_connected(block, connected_blocks,
                               forward=True, predicate=should_exec)  # Forwards

        # plan out an order of block .output() execution and propagation. From sources -> sinks
        # collect sources and ClockedBlocks with inputs ready (at this clock tick offset)
        plan = []
        for b in connected_blocks:
            if b.nin == 0 or (isinstance(b, ClockedBlock) and all(b.inputs)):
                in_clocked_plan[b] = True
                plan.append(b)

        # then propagate, updating plan as we go
        idx = 0
        while idx < len(plan):
            for outwires in plan[idx].outports:

                for w in outwires:
                    block: Block = w.end.block

                    # make sure we actually need to .output() this block on this clock tick.
                    # Should always be true
                    assert block in in_clocked_plan

                    if block in plan:
                        continue

                    block.inputs[w.end.port] = True

                    if all(block.inputs) and \
                            (block.clock is clock if isinstance(block, ClockedBlock) else True):
                        plan.append(block)
                        in_clocked_plan[block] = True
                        # reset the inputs
                        block.inputs = [None] * len(block.inputs)
            idx += 1

        plans[clock] = plan

    not_planned = set(
        block for block, planned in in_clocked_plan.items() if not planned)
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

    bd.start()
    
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
    scheduler.run()
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
            out = b.output(state.t)
            for (n, ws) in enumerate(b.outports):
                for w in ws:
                    w.end.block.inputs[w.end.port] = out[n]

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
    collected: Set[Block],
    forward: bool,
    predicate: Callable[[Block], bool]
):
    """Recurses connections in the block diagram, either forward or backward from a given block.
    Collects the blocks into the provided "collected" set.
    if forward=True, will recurse through outputs, otherwise will recurse through inputs
    """
    collected.add(block)

    if forward:
        for wires in block.outports:
            for wire in wires:
                if predicate(wire.end.block):
                    _collect_connected(
                        wire.end.block, collected, forward, predicate)
    else:
        for wire in block.inports:
            if predicate(wire.start.block):
                _collect_connected(
                    wire.start.block, collected, forward, predicate)
