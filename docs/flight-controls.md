# Flight controls and persistent settings

Checked on 2026-11-22 with Nick at the Windows client, version 20.04.3712181, for NIC-127. Key bindings were read from screenshots of the client's keyboard settings. Behaviour was reported by Nick while flying, first inside a station and later in space. All bindings are the client's current ones; none were changed for this project.

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
| Leap | Hold Space | A very rapid acceleration. It cannot be used inside a station. The ship can still be steered during it, but with aimed flight on it turns toward the camera direction much more slowly than in normal flight |

On the ship used for this check, the throttle has 35 steps forward and 9 steps in reverse. This may differ between ships. The ship's inventory is labelled "Creation", followed by an ID, and other pilots' ships of the same look carry a "[Creation]" tag, so the ship type appears to be Creation.

The character screen lists four piloting effects: thrust multiplier, warp speed multiplier, inertia modifier, and angular agility. All four were 0% on 2026-11-22, with the piloting skill at 0.03. If these rise, the ship will accelerate and turn differently, so each recording's metadata should note them.

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

Locking, checked in space on 2026-11-22:

- A target can be locked only within 100 km.
- Invulnerable targets cannot be locked.
- A lock takes some time to acquire after X is pressed.
- While the lock is being acquired, the screen looks the same as with no lock in the one screenshot taken. **Not checked**: whether an animation shows that a still frame missed.
- Once locked, a panel for the target appears at the right edge of the screen, with a round icon, the target's name, and its distance (for example "23 km"). Small corner marks also appear around the target's marker.

- Several targets can be locked at once. Each gets its own panel, in a row at the right edge. Three were locked in the screenshot.
- The panel gives the distance in metres when the target is under 10 km (for example "7,291 m"). The label on the target itself rounds to whole kilometres ("7 KM"), so the panel is the finer reading.
- Other pilots' ships can be locked. Their names then show on screen. Nick's decision on 2026-11-22: this is not a concern.
- One locked target is the selected one. Its panel has orange arrows around it.

The name and distance label on a target does not need a lock. It appears on whatever is nearest the centre circle, and it stays on anything Nick has clicked.

### The Supply Dock as a distance source

The Supply Dock is invulnerable, so it cannot be locked. Its label still gives a fine distance. Above the name, a line reads "OUT OF RANGE" with a distance in brackets:

| Distance | Line above the name | Label below the name |
| --- | --- | --- |
| Over 1 km | One decimal place of a kilometre, for example "(12.7 KM)", "(7.4 KM)", "(2.4 KM)" | Whole kilometres, for example "2 KM" |
| Under 1 km | Whole metres, for example "(181 M)", "(64 M)" | "0 KM" |

| In docking range | "IN RANGE" in orange, with no number | "0 KM" |

So the reading is good to 100 m beyond 1 km, and to 1 m inside it. Once the ship is in docking range the number is gone, and the "F Dock" hint under the label turns bright.

The lowest number seen before "IN RANGE" was 64 m. The bracketed number is probably the distance left to the edge of docking range, and not the distance to the dock itself. **Not checked**: this, and how large the docking range is.

### When a target is off-screen

Seen with a locked ship behind the camera. Its marker and label stay on screen, held near the edge on the side the target lies, and a small arrow appears beside the marker pointing outward. The label still shows the name and the distance. The lock panel is not affected.

**Not checked**: what an orange chevron on or just under the heading tape marks. It may be the bearing of the selected target.

The keyboard settings list an Approach command on Num +. It did nothing in three tries: with a target locked and Num Lock on, with Num Lock off, and with Num Lock on and no target locked. The game has no usable approach command on this client version.

## Settings that persist after input stops

This list decides the action format for the world model.

| Setting | Changed by | Values | Shown on screen |
| --- | --- | --- | --- |
| Throttle level | E, Q, Ctrl-Space | 35 steps forward, zero, 9 steps reverse on this ship | The throttle gauge at the left, marked R, 0, and MAX |
| Aimed flight | C | On or off | The hint bar, and the two circles when on |
| Camera direction | Mouse | Continuous | With aimed flight on, the red circle's offset from the centre |
| View | F1, F2 | CAM or TAC | The whole display changes |
| Locked targets | X | None, one, or several | A panel for each at the right edge, and corner marks around each target's marker |
| Equipped module | 1 to 8 | A module or none | The module slot is highlighted, and the hint bar changes to "Fire", "Unequip", and "Leap" |
| Approach command | Num + | Does nothing | |
| Zoom | Right mouse button and wheel | **Not checked** whether it persists | |

Inputs that do not persist: the brake, and the turn, strafe, and roll keys. All act only while held, apart from the ship's inertia.

## What the flight display shows

Seen in the screenshots of the CAM view. Positions and sizes will be measured from recordings.

- **Throttle gauge.** A vertical bar left of centre, marked MAX at the top, 0, and R at the bottom.
- **Speed.** A number beside the throttle gauge, in metres a second, for example "117 M/S".
- **Target.** A name label on the target, with its distance below, for example "6 KM". A second line can appear above the name, for example "OUT OF RANGE (12.7 KM)".
- **Heading tape.** A compass strip across the top, in degrees, with small markers on it.
- **Hint bar.** Key hints along the bottom, which change with the steering mode. With a module equipped, the bar shows only "Fire", "Unequip", and "Leap", so the steering mode cannot be read from it then.
- **Objectives panel.** At the top left when the game has given objectives. It changes size as objectives change.
- **Small white arrows.** Several sit in a ring around the centre of the screen. They mark objects that are off-screen, as described above.
- **Panels.** Signature, fuel, shell, ship hit points, and capacitor at the bottom. Chat tabs at the top right. Module slots 1 to 8 at the bottom right.

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
