# Client settings

Read on 2026-11-22 from screenshots of the Display & Graphics tab, on client version 20.04.3712181, for NIC-127. Every recording and every flight uses the same settings. Each recording's metadata should note them, so a change is caught.

## Display

| Setting | Value on 2026-11-22 |
| --- | --- |
| Display Mode | Fullscreen. The other choices are Windowed and Fullscreen Borderless |
| Adapter Resolution | 3840 by 2160 |
| UI Scaling | 200% |
| Display Adapter | NVIDIA GeForce RTX 5090 |
| V-Sync | Off |
| Upscaling | Off |
| Upscaling Setting | Not available |
| Frame Generation | Off |

The game is on one monitor of several. The Windows desktop is 6000 by 3840, and the game fills the area from x 0 to 3839 and y 768 to 2927.

## Graphics

All ten quality settings are High: Anti-Aliasing, Post Processing, Shader Quality, Texture Quality, LOD Quality, Terrain Detail, Shadow Quality, Ambient Occlusion, Volumetric Effects Quality, and Reflections. Experimental Lighting is ticked. Brightness was not opened.

## Camera

| Setting | Value on 2026-11-22 |
| --- | --- |
| Camera Center H | Centre of the slider |
| Camera Center V | About three quarters of the way toward Down |
| Camera Shake | About 50% |
| Camera Bobbing | On |
| Invert Zoom Direction | Off |
| Offset Interface With Camera | Off |
| Dynamic Camera Movement | On |
| Scroll between view modes | Off |

The slider positions are read by eye from a screenshot.

## During flight

- CAM view (F1).
- Aimed flight on at the start of every session.
- No module equipped, so the hint bar shows the steering mode.
- No panels open. The Objectives panel at the top left closes or changes with the game's tutorial, so it should be collapsed or finished before recording.

## Proposed changes, not decided

These are for Nick to decide before the first recording.

1. **Display Mode to Fullscreen Borderless.** Screen capture tools are more reliable with a borderless window than with exclusive fullscreen, and switching to another window is smoother. To be tested when the recording tool is built (NIC-116).
2. **Camera Shake to Off, and Camera Bobbing and Dynamic Camera Movement off.** These move the camera in ways the pilot's inputs do not cause. The world model has to predict the next frame from the inputs, and the readers measure the red circle's offset from the centre, so less unprompted camera movement helps both. **Not checked**: what each of the three does in flight.

## Not checked

- The General tab of the settings, which may hold more options that change the flight display.
- The Brightness setting.
