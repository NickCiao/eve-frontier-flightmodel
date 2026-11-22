# Flight controls and persistent settings

Checked on 2026-11-22 with Nick at the Windows client, version 20.04.3712181, for NIC-127. Key bindings were read from screenshots of the client's keyboard settings. Behaviour was reported by Nick while flying inside a station. All bindings are the client's current ones; none were changed for this project.

Items marked **not checked** still need a test.

## How steering works

The ship has two steering modes. **Toggle aimed flight** (C) switches between them.

| | Aimed flight on | Aimed flight off |
| --- | --- | --- |
| Mouse | Turns the camera. The ship then turns until its nose points where the camera points | Turns the camera only. The ship keeps its heading |
| W / S | Strafe up / down | Pitch up / down |
| A / D | Strafe left / right | Yaw left / right |
| Alt-W / S / A / D | Not bound in this mode | Strafe up / down / left / right |
| Alt-Q / Alt-E | Roll left / right | Roll left / right |

Two circles show on screen when aimed flight is on:

- **The centre circle** is where the camera points. It is always at the centre of the screen.
- **The red circle** is where the ship's nose points. After the mouse moves, it sits away from the centre and drifts back to it as the ship turns.

The camera stays where the mouse left it in both modes.

This differs from the Notion page, which describes the mouse placing a marker that the ship turns toward. The mouse turns the camera, and the marker that moves on screen is the ship's nose. Two consequences:

- The steering action is mouse movement (a camera rotation), in both modes.
- The red circle's offset from the centre is the camera's offset from the ship's heading. It can be read from the frame when aimed flight is on.

The current mode can be read from any frame. The hint bar at the bottom of the screen shows "C Enable Aimed Flight" with yaw, pitch, and strafe hints when the mode is off, and "C Disable Aimed Flight" with "W A S D Strafe" when it is on.

Turn, strafe, and roll keys act only while held. The ship has inertia, so a turn or roll does not stop the moment the key is released.

## Throttle and speed

| Action | Key | Behaviour |
| --- | --- | --- |
| Accelerate | E | One tap raises the throttle one step, and it stays there |
| Decelerate | Q | One tap lowers the throttle one step. Below zero is reverse |
| Brake | Ctrl | Slows the ship to a stop while held. On release the ship speeds up again to the throttle setting |
| Stop Ship | Ctrl-Space | Sets the throttle to zero |
| Leap | Space | A very rapid acceleration. The ship can still be steered during it. **Not checked**: it cannot be used inside a station |

On the ship used for this check, the throttle has 35 steps forward and 9 steps in reverse. This may differ between ships. **Not checked**: the ship's name.

## Camera and views

| Action | Key | Notes |
| --- | --- | --- |
| CAM view | F1 | The normal flight view, with the full flight display |
| TAC view | F2 | A greyscale view with the ship highlighted. It hides the throttle gauge, the heading tape, and the two circles |
| Reset camera | Backspace | **Not checked** |
| Zoom | Hold the right mouse button | Zooms in. The mouse wheel changes the zoom while the button is held. **Not checked**: whether the zoom stays after the button is released |

"Free Look" and "Thrust Backward" are listed under assisted flight and have no key bound.

## Targets and the game's own approach command

| Action | Key |
| --- | --- |
| Toggle lock target | X |
| Unlock target | Shift-X |
| Unlock all targets | Ctrl-Shift-X |
| Approach | Num + |
| Toggle waypoint | T |
| Primary action (shown as "Dock" near a dock) | F |

The game has its own approach command. **Not checked**: what it does, how it is cancelled, and where it stops the ship.

## Settings that persist after input stops

This list decides the action format for the world model.

| Setting | Changed by | Values | Shown on screen |
| --- | --- | --- | --- |
| Throttle level | E, Q, Ctrl-Space | 35 steps forward, zero, 9 steps reverse on this ship | The throttle gauge at the left, marked R, 0, and MAX |
| Aimed flight | C | On or off | The hint bar, and the two circles when on |
| Camera direction | Mouse | Continuous | With aimed flight on, the red circle's offset from the centre |
| View | F1, F2 | CAM or TAC | The whole display changes |
| Locked target | X | A target or none | **Not checked** |
| Approach command | Num + | Running or not | **Not checked** |
| Zoom | Right mouse button and wheel | **Not checked** whether it persists | |

Inputs that do not persist: the brake, and the turn, strafe, and roll keys. All act only while held, apart from the ship's inertia.

## What the flight display shows

Seen in the screenshots of the CAM view. Positions and sizes will be measured from recordings.

- **Throttle gauge.** A vertical bar left of centre, marked MAX at the top, 0, and R at the bottom.
- **Speed.** A number beside the throttle gauge, in metres a second, for example "117 M/S".
- **Target.** A name label on the target, with its distance below, for example "6 KM". A second line can appear above the name, for example "OUT OF RANGE (12.7 KM)".
- **Heading tape.** A compass strip across the top, in degrees, with small markers on it.
- **Hint bar.** Key hints along the bottom, which change with the steering mode.
- **Panels.** Signature, fuel, shell, ship hit points, and capacitor at the bottom. Chat tabs at the top right. Module slots 1 to 8 at the bottom right.

**Not checked**: what appears when the target is off-screen.

## Full key list for flight

From the Navigation, Manual Flight, Assisted Flight, and Combat tabs of the keyboard settings.

| Command | Key | Tab |
| --- | --- | --- |
| Accelerate | E | Navigation |
| Decelerate | Q | Navigation |
| Stop Ship | Ctrl-Space | Navigation |
| Brake | Ctrl | Navigation |
| Leap | Space | Navigation |
| Toggle aimed flight | C | Navigation |
| Activate CAM view | F1 | Navigation |
| Activate TAC view | F2 | Navigation |
| Reset camera | Backspace | Navigation |
| Zoom In / Zoom Out | Wheel up / Wheel down | Navigation |
| Toggle waypoint | T | Navigation |
| Pitch Up / Pitch Down | W / S | Manual Flight |
| Yaw Left / Yaw Right | A / D | Manual Flight |
| Roll Left / Roll Right | Alt-Q / Alt-E | Manual Flight, Assisted Flight |
| Strafe Up / Down / Left / Right | Alt-W / Alt-S / Alt-A / Alt-D | Manual Flight |
| Increase / Decrease Pitch, Increase / Decrease Yaw | Not bound | Manual Flight |
| Strafe Up / Down / Left / Right | W / S / A / D | Assisted Flight |
| Free Look | Not bound | Assisted Flight |
| Thrust Backward | Not bound | Assisted Flight |
| Approach | Num + | Combat |
| Toggle lock target | X | Combat |
| Unlock target | Shift-X | Combat |
| Unlock all targets | Ctrl-Shift-X | Combat |
| Toggle radial menu | Middle mouse button | Modules |

The keyboard settings call the two modes "Manual Flight" and "Assisted Flight". By the bindings, assisted flight is aimed flight on, and manual flight is aimed flight off.

Keys that also do something else: Space is also "Map: Select System", and Q, E, W, A, S, D, and C drive menus when a window or the radial menu has focus.
