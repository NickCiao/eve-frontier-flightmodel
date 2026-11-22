# capture

The Windows side of the project: everything that touches the game client. For now it holds the recording tool and the replay viewer (Stage 1, NIC-116). Nothing here sends input to the game.

The files a recording produces are described in [`docs/recording-format.md`](../docs/recording-format.md).

## Setup

Needs Windows 11, an NVIDIA GPU, uv, and ffmpeg on the PATH.

```powershell
cd capture
uv sync
```

## Record

Start the game first, in Fullscreen Borderless, then:

```powershell
uv run eve-record --target "Supply Dock" --character "<name>" --system "<system>"
```

- Stop with **F10**, or Ctrl-C in the terminal. `--stop-key` changes the key.
- Sessions go to `F:\eve-flight-recordings`. `--out` or the `EVE_RECORDINGS_DIR` variable changes that.
- Keys and mouse movement are logged only while the game is in front.
- `--duration 600` stops after ten minutes.
- `--any-window --no-input` records the main monitor without the game, for testing the tool.

Before each session: CAM view (F1), aimed flight on, no module equipped, no panels open, and the target clicked once so its label stays.

## Replay

```powershell
uv run eve-replay F:\eve-flight-recordings\<session>
```

Space plays or pauses. `.` and `,` step one frame. `]` and `[` jump ten seconds. Q quits. The panel at the top shows the keys held at each frame, the keys that changed since the previous frame, and the mouse movement since the previous frame.

## Files

| File | Purpose |
| --- | --- |
| `eve_capture/record.py` | The recorder |
| `eve_capture/rawinput.py` | Key and mouse logging through Windows Raw Input |
| `eve_capture/win.py` | Finding the game window and its monitor |
| `eve_capture/replay.py` | The replay viewer |
| `client_settings.json` | The fixed client settings, copied into each session |
