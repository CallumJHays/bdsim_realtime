import utime
from typing import Callable, Dict, List, Optional, Set
import math
import gc

from micropython import schedule
from machine import Timer

from bdsim import Block, BlockDiagram, BDSimState
from bdsim.components import Clock, ClockedBlock, SinkBlock, SourceBlock


def _clocked_plans(bd: BlockDiagram):
    plans: Dict[Clock, List[Block]] = {}

    prev_clock_period = 0
    # track to make sure we're actually executing all blocks on clock cycles properly.
    # otherwise the realtime blockdiagram is not fit for realtime execution
    in_clocked_plan: Dict[Block, bool] = {
        block: False for block in bd.blocklist if not block.sim_only}

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
            return not b.sim_only \
                and not in_clocked_plan[b] \
                and (not isinstance(b, ClockedBlock) or b.clock is clock)

        # Recurse backwards and forwards to collect these
        for block in clock.blocklist:
            _collect_connected(block, connected_blocks,
                               forward=False, predicate=should_exec)  # Backwards
            _collect_connected(block, connected_blocks,
                               forward=True, predicate=should_exec)  # Forwards

        # plan out an order of block .output() execution and propagation. From sources -> sinks
        # collect sources and clockedblocks
        plan = []

        for b in connected_blocks:
            if isinstance(b, (ClockedBlock, SourceBlock)):
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
                            (not isinstance(block, ClockedBlock) or block.clock is clock):
                        plan.append(block)
                        in_clocked_plan[block] = True
                        # reset the inputs
                        block.inputs = [None] * len(block.inputs)
            idx += 1

        plans[clock] = plan

    not_planned = set(
        block for block, planned in in_clocked_plan.items() if not planned)
    assert not any(not_planned), """Blocks {} do not depend on or are a dependency of any ClockedBlocks.
This is required for its real-time execution.
Mark the blocks as sim_only=True if they are not required for realtime execution, or declare them within the `with bdsim.simulation_only: ...` context manager""" \
    .format(not_planned)

    return plans


# track microseconds globally to calculate dt t then update state.t
t_us = None


def run(bd: BlockDiagram, max_time: Optional[float] = None):
    global t_us
    state = bd.state = BDSimState()
    state.T = max_time

    if not bd.compiled:
        bd.compile()
        print("Compiled!\n")

    clock2plan = _clocked_plans(bd)

    bd.reset()
    bd.start()

    print("Executing {}:".format("for {} seconds:".format(
        max_time) if max_time else "forever"))

    timers: List[Timer] = []
    for idx, (clock, plan) in enumerate(clock2plan.items()):
        print("{}:{}".format(
            clock,
            ''.join('\n\t{}. {}{}'.format(idx, b, ' (clocked)' if isinstance(b, ClockedBlock) else '')
                    for idx, b in enumerate(plan))))
        timers.append(Timer(idx))

    t_us = utime.ticks_us()
    state.t = 0

    print('t_us', t_us)
    for timer, (clock, plan) in zip(timers, clock2plan.items()):
        now = utime.ticks_us()
        utime.sleep_us(utime.ticks_diff(
            t_us + math.ceil(clock.offset * 1e6), now))
        print('starting timer for clock', clock, 'at',
              utime.ticks_us(), 'beforesleep', now)

        # inner fn to closure the variables
        def kickoff(clock, plan, state, timer):
            exec_plan = create_exec_plan(
                clock=clock, plan=plan, state=state, timer=timer)
            timer.init(
                period=math.ceil(clock.T * 1e3),  # period is in ms
                callback=lambda _: schedule(exec_plan, None)
            )
        kickoff(clock, plan, state, timer)

    print("System time (utime.ticks_us()) is now {}. Running scheduler.run()!".format(t_us))
    if max_time:
        print('sleeping for ', math.ceil(max_time * 1e3), 'ms')
        utime.sleep_ms(math.ceil(max_time * 1e3))
    else:
        while not state.stop:
            utime.sleep(1)  # should this be higher?

    print('stopping all hardware timers')
    # stop all timers
    for timer in timers:
        timer.deinit()
    print("Realtime Execution Stopped")


def create_exec_plan(
    clock: Clock,
    plan: List[Block],
    state: BDSimState,
    timer: Timer
):

    executed_once = False

    def exec_plan(arg: None):
        global t_us
        nonlocal executed_once

        now_us = utime.ticks_us()
        dt_us = utime.ticks_diff(now_us, t_us)
        t_us = now_us
        state.t += dt_us * 1e-6
        print('executing plan', plan, 'at time', state.t)

        try:
            # execute the 'ontick' steps for each clock, ie read ADC's output PWM's, send/receive datas
            for b in clock.blocklist:
                # if this block requires inputs, only run .next() the second time this was scheduled.
                # this way, its data-dependencies are met before .next() executes
                if executed_once or isinstance(b, SourceBlock):
                    b._x = b.next()

            # now execute the given plan
            for b in plan:
                if isinstance(b, SinkBlock):
                    b.step()  # step sink blocks
                else:
                    # propagate all other blocks
                    out = b.output(state.t)
                    for (n, ws) in enumerate(b.outports):
                        for w in ws:
                            w.end.block.inputs[w.end.port] = out[n]

        except Exception as e:
            state.stop = e
            timer.deinit()
            raise e

        executed_once = True
        print('plan execution took', utime.ticks_diff(
            utime.ticks_us(), now_us) * 1e-6, 'secs\n')

        if state.stop:  # don't need to check for max_time as that's done in the mainloop in run()
            timer.deinit()
            print('Stopped due to', state.stop)

    return exec_plan


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
