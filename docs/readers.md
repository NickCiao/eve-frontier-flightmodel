# State readers

Written on 2026-11-22 for NIC-117. The readers are in [`capture/eve_capture/readers.py`](../capture/eve_capture/readers.py). They turn one frame of the flight display into numbers. They were built and checked on the ten-minute session `20261122-190951`.

The readers are for the hand-written controller and for checking. The world model is never trained on them.

They assume the client settings in [`client-settings.md`](client-settings.md): 3840 by 2160, UI scaling 200%. Positions are fixed in those pixels.

## What is read

Each reading is a value and a confidence from 0 to 1. A missing value means the reader did not find the thing on screen.

| Reading | Meaning | Read from |
| --- | --- | --- |
| `speed_mps` | Speed in metres a second. Negative in reverse | The white number above the orange marker beside the throttle gauge |
| `speed_marker_y` | The marker's row on screen. It slides up the gauge with speed | The marker |
| `throttle` | From -1 (full reverse) to 1 (full forward) | How far the gauge is filled with bright orange |
| `label_x`, `label_y` | The centre of the target's name on screen, in pixels | Matching an image of the name |
| `range_m` | Metres left to the edge of docking range. 0 when in range | The "OUT OF RANGE" line above the name |
| `in_range` | True when the line says "IN RANGE" | The same line |
| `nose_dx`, `nose_dy` | Where the ship's nose points, in pixels right of and below the screen centre | The nose circle, a thin orange ring 100 pixels in radius |
| `target_dx`, `target_dy` | The target's name relative to the nose, in pixels | The two readings above |
| `closing_mps` | Closing speed toward the target, in metres a second | The change in `range_m` over about a second |

How these map to the quantities in NIC-117:

- **Speed** is `speed_mps`.
- **Distance to the selected target** is `range_m`. It is the distance to the edge of docking range, which is what the display shows.
- **Camera offset from the ship's heading** and **aim marker position** are the same thing in this game: `nose_dx` and `nose_dy`. The mouse turns the camera, and the nose circle shows where the ship points relative to it.
- **Direction to the target relative to the nose** is `target_dx` and `target_dy`.
- **Closing speed** is `closing_mps`.

## Things to know

- **The nose circle is only drawn while the camera is turned away from the heading.** It was found in 94 of 601 sampled frames. When it is missing, `target_dx` and `target_dy` assume the nose is at the screen centre, at half confidence.
- **Offsets are in pixels, not degrees.** The camera's field of view is not known. **Not checked.**
- **The target's position is the centre of its name**, which sits a little below the object itself.
- **The range line is sometimes hidden.** The game draws it only on some frames, and the centre circle or another marker can cover it. The reader then gives no value, or a value with confidence under 0.5 when a digit may be covered.
- **Speed is shown in thousands above 999**, as "1.34K M/S". The reader gives 1340, so it is good to 10 m/s there.
- **Range steps in 100 m beyond 1 km**, so `closing_mps` is coarse at long range.
- **Nothing is read while docked or during a white-out.** The display is hidden then.
- **Other targets** need an image of the target's name as the label shows it, passed as `target_template`. Nothing else in the readers is specific to the Supply Dock. A target with no range line gives `label_x` and `label_y` only.

## How the text is read

The display uses one fixed-size font, so the readers match each character's shape directly. The shapes were collected from the recording and are in `capture/eve_capture/assets/glyphs.npz`. Matching uses normalised correlation, so it does not depend on how bright the text is.

## The hand check on 2026-11-22

200 frames were picked at random from the ten-minute session. For each, the speed text and the range line were cropped from the frame and compared by eye with the reading. The check was done by the Windows session, not by Nick.

| Reading | Result |
| --- | --- |
| Speed | 194 of 196 frames with a visible speed were read correctly. The 2 wrong ones had a bright light over the start of the number: a minus sign was missed on one, and a leading digit on the other |
| Speed, after the fix below | The same 2 are still wrong, but now carry a confidence of 0.37, against about 0.9 for a clean reading |
| Range, confidence 0.5 or more | All correct |
| Range, confidence under 0.5 | 2 frames, both wrong, both with a digit covered. This is what the low confidence is for |
| Range, no value where the line was partly visible | 3 frames, each with something drawn over the line |
| In range | All correct |
| Display hidden | 4 frames, all correctly read as nothing |

**Fix after the check.** When something bright sits just left of the speed and is not a minus sign, the speed's confidence is cut to 0.4 times its value.

A controller should ignore readings under 0.5 confidence and carry the last good value forward.

**Not checked by hand:** the throttle and the nose circle on these 200 frames. The nose circle was checked separately on about 130 detections across the session: every score of 0.86 or more was a real circle, and every score of 0.66 or less was not. The cut is at 0.75.

## Speed of the readers

About 74 ms a frame for all readings together, on one CPU core, measured on recorded frames. That is inside the 100 ms a frame allows at 10 frames a second, with little to spare.

**Not checked**: the readers running live beside the recorder and the game. This is the second half of NIC-117's finish line.

## Running them

```powershell
uv run eve-read F:\eve-flight-recordings\<session>
```

This writes `readings.csv` in the session folder: the frame, its time, then a value and a confidence for each reading.

## Still open

- The live speed test.
- A hand check of the throttle reading.
- What the two small orange scales at the top and right of the display show. They are not read.
- Reading the steering mode from the hint bar. It is not in NIC-117's list, but the controller will want it.
- Turning pixel offsets into angles.
