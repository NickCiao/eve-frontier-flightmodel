# Handoff to the Windows session

Written by the WSL session on 2026-11-22. It covers what is done, what the Windows session owns next, and what Nick needs to be walked through.

## Read first

1. The Notion page [EVE AI Program: Flight World Model Experiment](https://app.notion.com/p/418e33e50bb181658113d9561988b084). It was rewritten on 2026-11-18. It now compares a hand-written controller with a LeWM world model, and it allows automated input on Nick's account with Nick at the keyboard.
2. [`CLAUDE.md`](../CLAUDE.md) in this repo, for the rules and conventions.
3. The Linear project [EVE Frontier Flight Model](https://linear.app/nciao/project/eve-frontier-flight-model-33869fa89756). It is the control plane. Pick up work from it and report back to it.

## Where things stand

| Item | State |
| --- | --- |
| Linear project, an issue for each stage (NIC-115 to NIC-123) | Done |
| Repo scaffold | Done. Nothing is cloned on the Windows side yet |
| LeWM's four settings (NIC-126) | Confirmed. All match the Notion page |
| LeWM reproduced on PushT in WSL (NIC-125) | Done. 92%, the same as the published checkpoint |
| Flight controls, approach task, client settings, screenshots (NIC-127) | Not started. Needs Nick and the game client |
| Split of work confirmed between the sessions (NIC-124) | Open |
| Stage 5 and 6 groundwork | On hold at Nick's request |

## The split of work

- **Windows session:** everything that touches the game client. Capture, the readers, input, and the live loop. Code goes in `capture/`.
- **WSL session:** LeWM, training, and offline evaluation. Code goes in `model/`.

Please confirm this split, or say what you would change, in a comment on NIC-124.

One thing to settle there: where recordings live. They must stay out of git. WSL can read any Windows folder under `/mnt/c`, so a Windows folder works for both sessions. Reading speed from WSL has not been measured.

## What the Windows session owns next

### 1. Finish Stage 0 with Nick (NIC-127)

Nick needs to be walked through these with the game client open. Write the answers into `docs/` with the date, and close NIC-127 with a summary.

1. **Flight controls.** Which keys and mouse movements do what. How throttle, pitch, yaw, and roll work. The mouse steers by aim point: it places a marker, and the ship turns toward it. The mouse can be decoupled from steering with a toggle, so that it only moves the camera.
2. **Persistent settings.** Every setting that stays after the input stops, such as the throttle level, the decoupling toggle, or a directional lock. This list decides the action format for the world model, so the WSL session needs it.
3. **The approach task.** Where it is flown, the target, the starting distance, and what counts as arrived (a distance and a speed). A quiet place away from other players. Note whether the game has its own approach command.
4. **Client settings.** Resolution, UI layout, graphics settings, and camera mode. Every recording and every flight uses the same ones. Panels stay closed during flight.
5. **What the screen shows.** The speed readout, the target's distance, the aim marker, the target's marker, and what appears when the target is off-screen. Nick adds annotated screenshots to the repo. His are from the macOS client, so positions and sizes come from the Windows recordings.

### 2. Stage 1: the recording tool (NIC-116)

- Frames of the whole client window at native resolution, 10 frames a second, stored uncropped as high-quality video or JPEG. Recording must not visibly slow the game.
- Every key and mouse press and release, with its time, on the same clock as the frames.
- The client's own log output, where it can be saved without touching the client.
- A small metadata file for each session. Every session starts with the mouse coupled to steering.
- A replay viewer that shows the frames with the inputs drawn on top.

Done when a 10-minute session replays with inputs lined up within one frame.

Stages 2 and 3 (the readers, the input tool, and the controller) follow. They are in NIC-117 and NIC-118.

## What the WSL session needs from the Windows side

- The recording format, as soon as it is fixed: file layout, frame encoding, timestamps, and the input log's fields. Stage 5 converts recordings to LeWM's HDF5 format.
- The persistent settings from step 2 above.

For reference, LeWM takes 224 by 224 frames, groups five frames into one step, and takes each step's action as the five per-frame actions joined together. Details are in [`lewm-setup.md`](lewm-setup.md).

## Facts about this PC

Checked from WSL on 2026-11-18, except where a date is given.

- Windows side: Python 3.12 and uv, git, GitHub CLI logged in as `NickCiao`, ffmpeg, MSVC build tools, and the Windows 11 SDK.
- GPU PyTorch is not installed in any permanent Windows environment. The earlier check was in a throwaway folder.
- WSL has 40 GB of memory since 2026-11-22. Training uses about 13.7 GB of the 5090's 32 GB, so a live loop and a training run would share the GPU if they ran together.
- One NVIDIA driver error hung a WSL training run on 2026-11-18. The cause is not known. If the Windows side sees GPU errors, note them in Linear.

## Reaching the WSL session

It is named `nickchow-bigboy-WSL`. When the Windows session was last checked, on 2026-11-22, it was not listed as reachable, so this note was written in place of a message. Linear comments work when messaging does not.
