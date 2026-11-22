# Client settings

Read on 2026-11-22 from screenshots of the Display & Graphics and General tabs, on client version 20.04.3712181, for NIC-127. Every recording and every flight uses the same settings. Each recording's metadata should note them, so a change is caught.

## Display

| Setting | Value on 2026-11-22 |
| --- | --- |
| Display Mode | Fullscreen Borderless. Nick changed it from Fullscreen on 2026-11-22. The other choice is Windowed |
| Adapter Resolution | 3840 by 2160 |
| UI Scaling | 200% |
| Display Adapter | NVIDIA GeForce RTX 5090 |
| V-Sync | Off |
| Upscaling | Off |
| Upscaling Setting | Not available |
| Frame Generation | Off |

The game is on one monitor of several, and fills it. That monitor is the primary one, 3840 by 2160 with its top left at 0, 0. The recorder confirmed this in borderless mode on 2026-11-22. In a Win + PrtScn screenshot of the whole desktop, which is 6000 by 3840, the game is the area from x 0 to 3839 and y 768 to 2927.

## Graphics

All ten quality settings are High: Anti-Aliasing, Post Processing, Shader Quality, Texture Quality, LOD Quality, Terrain Detail, Shadow Quality, Ambient Occlusion, Volumetric Effects Quality, and Reflections. Experimental Lighting is ticked. The Brightness slider is at its centre.

## Camera

| Setting | Value on 2026-11-22 |
| --- | --- |
| Camera Center H | Centre of the slider |
| Camera Center V | About three quarters of the way toward Down |
| Camera Shake | Off. It was about 50% |
| Camera Bobbing | Off. It was on |
| Invert Zoom Direction | Off |
| Offset Interface With Camera | Off |
| Dynamic Camera Movement | Off. It was on |
| Scroll between view modes | Off |

The slider positions are read by eye from a screenshot. Nick turned off the shake, bobbing, and dynamic movement on 2026-11-22, and reported the change. No screenshot was taken after it.

## During flight

- CAM view (F1).
- Aimed flight on at the start of every session.
- No module equipped, so the hint bar shows the steering mode.
- No panels open. The Objectives panel at the top left closes or changes with the game's tutorial, so it should be collapsed or finished before recording.

## General tab

| Setting | Value on 2026-11-22 |
| --- | --- |
| Cursor Size | Normal |
| Mouse Sensitivity | Centre of the slider |
| ADS Sensitivity | Centre of the slider |
| Mouse Smoothing | Centre of the slider, between Smooth and Stiff |
| Invert Y-axis | Off |
| Tooltips Delay | Near None |
| Show HUD shortcut hints | On |
| Auto Target Back | 0 targets |
| Enable window blur | On |
| Transparency | Full |
| Light Mode Transparency | Full |
| Color Blind Mode | Off |
| Notifications Enabled | On |

Three of these matter for the project:

- **Show HUD shortcut hints** must stay on. The hint bar is how the steering mode is read from a frame.
- **Mouse Sensitivity** sets how far the camera turns for a given mouse movement. The input tool and the recordings depend on it, so it must not change.
- **Mouse Smoothing** may spread a mouse movement over later frames. **Not checked**: how much delay it adds. This matters when the recorded inputs are lined up with the frames.

## Why these changes were made

Nick made both on 2026-11-22, before the first recording.

1. **Fullscreen Borderless.** Screen capture tools are more reliable with a borderless window than with exclusive fullscreen, and switching to another window is smoother. To be confirmed when the recording tool is built (NIC-116).
2. **Camera Shake, Camera Bobbing, and Dynamic Camera Movement off.** These move the camera in ways the pilot's inputs do not cause. The world model has to predict the next frame from the inputs, and the readers measure the red circle's offset from the centre, so less unprompted camera movement helps both.

## Not checked

- How the ship feels in flight with the three camera settings off.