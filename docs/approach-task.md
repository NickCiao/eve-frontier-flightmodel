# The approach task

Agreed with Nick on 2026-11-22 for NIC-127, on client version 20.04.3712181. The screen readings it relies on are described in [`flight-controls.md`](flight-controls.md).

## The task

Fly the ship from a standing start to the Supply Dock and stop there.

| Item | Value | State |
| --- | --- | --- |
| Target | The Supply Dock in the starting area | Agreed |
| Start | About 10 km from the dock, stopped, facing a random direction | Proposed |
| Arrived | The dock's label shows "IN RANGE" and the speed is under 10 m/s | Proposed |
| Failed | Not arrived within a time limit | The limit is set after a few hand-flown runs |
| Setup | Nick clicks the dock once so its label stays on screen. Aimed flight is on. No module is equipped. CAM view (F1) | Proposed |

The game has no usable approach command, so there is no built-in pilot to compare against.

## Why the Supply Dock

- It is always there and does not move.
- Its label gives a distance without a lock: to 100 m beyond 1 km, and to 1 m inside it.
- The game itself marks arrival, by changing the label to "IN RANGE".

Its drawbacks:

- It cannot be locked, so there is no lock panel for it.
- Other pilots fly near it. Three were within 8 km when this was checked.
- Once "IN RANGE" shows, the distance number is gone. Overshoot inside docking range cannot be read from the label.

## Other targets

Nick suggested varying the target, using objects outside the starting area. Not decided. What a target needs:

- It stays in one place.
- The screen shows its distance finely enough to judge arrival. A locked target's panel gives metres under 10 km. A target that cannot be locked gives only whole kilometres, unless it has a range line like the dock's.

**Not checked**: which objects outside the starting area meet both.

## Still open

- How large docking range is, and whether the bracketed distance counts down to its edge or to the dock.
- The time limit.
- Whether the start distance and arrival speed above are right once Nick has flown the task by hand.
