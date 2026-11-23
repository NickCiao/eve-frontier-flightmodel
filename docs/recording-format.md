# Recording format

Format version 1, written on 2026-11-22 for NIC-116. The recorder is in [`capture/`](../capture/README.md). It was tested on 2026-11-22 with a one-minute recording of the game, and a ten-minute one, both described at the end.

The format may still change until that test is done. `meta.json` carries `format_version`, and any change raises it.

## Where sessions live

Each session is a folder under `F:\eve-flight-recordings`, which WSL sees as `/mnt/f/eve-flight-recordings`. The folder's name is the local start time, for example `20261122-190000`. Nothing here is in git.

```
20261122-190000/
  video.mkv       the frames
  frames.csv      one row for each frame, with its time
  inputs.csv      one row for each key or mouse event, with its time
  meta.json       the session's settings, task, and totals
  client-logs/    the game's own log files written during the session
```

## The clock

Every `t_ns` in the session is `time.perf_counter_ns()` on the recording PC, in nanoseconds. Frames and inputs share it, so they can be compared directly. It has no meaning outside the session. `meta.json` gives `clock.t0_ns` and `started_utc`, read at the same moment, to convert to wall-clock time.

## video.mkv

| Property | Value |
| --- | --- |
| Content | The whole game window, uncropped, at its own resolution (3840 by 2160) |
| Codec | HEVC, from the NVIDIA encoder, at a constant quality (`qp` 18) |
| Colour | 4:4:4, 8 bits. Colour is not halved, so small red and orange text stays sharp |
| Frame rate | 10 frames a second, nominal |
| Keyframes | One every 10 frames, and no B-frames, so seeking is quick |
| Size | 650 MB for one minute of game footage, so about 6.5 GB for ten minutes |

The video's own timestamps are nominal. The true time of each frame is in `frames.csv`.

## frames.csv

Row `n` is frame `n` of the video, counting from 0.

| Column | Meaning |
| --- | --- |
| `frame` | The frame's index in the video |
| `t_ns` | When the frame was taken from the screen |
| `new` | 1 if the screen had changed since the previous grab. 0 if the previous image was written again |

Frames are taken on a 100 ms grid. If the recorder falls behind by a whole tick, it skips that tick and does not write a frame for it. So the gap between two rows is normally 100 ms and can be 200 ms or more. `meta.json` counts the skipped ticks.

## inputs.csv

One row for each event, in time order. Empty cells are fields that do not apply to the row's kind.

| Column | Used by | Meaning |
| --- | --- | --- |
| `t_ns` | all | When the event arrived |
| `kind` | all | `key`, `move`, `button`, `wheel`, or `focus` |
| `name` | key, button | The key's name in lower case (`w`, `ctrl`, `space`, `f1`, `num+`), or the button (`left`, `right`, `middle`, `x1`, `x2`) |
| `state` | key, button, focus | `down` or `up`. For focus: `game` or `other` |
| `dx`, `dy` | move | The mouse's own movement counts since its last report. Right and down are positive |
| `delta` | wheel | 120 for one notch away from the user, -120 for one toward |
| `vkey`, `scan` | key | The Windows virtual-key code and the scan code |

Things to know:

- **Mouse movement is relative.** It comes from the Windows Raw Input API, which is what the game reads. There is no cursor position. A mouse can report up to 1,000 times a second, so sum `dx` and `dy` over a frame's interval.
- **Keys are logged on change only.** A held key gives one `down` and one `up`. The keyboard's own repeat is dropped.
- **Left and right Ctrl, Shift, and Alt share a name.** The scan code tells them apart.
- **Only the game's input is kept.** Events are dropped while another program is in front. A `focus` row marks each switch, and every held key and button gets an `up` row when the game loses focus.
- **The stop key is not logged.** It is F10 unless changed, and `meta.json` names it.

The inputs for frame `n` are the events with `t_ns` after frame `n-1`'s time and up to frame `n`'s time.

## meta.json

| Field | Meaning |
| --- | --- |
| `format_version` | 1 |
| `session_id`, `started_local`, `started_utc` | When the session began |
| `clock` | `t0_ns` and `started_unix`, read together |
| `video` | The encoding settings above, with the width and height |
| `capture` | The capture method, the monitor, and the area recorded |
| `inputs` | The method, the stop key, and whether input was logged |
| `task` | `target`, `arrival`, `distance_source`, and `pilot` (`human`, `controller`, or `world-model`) |
| `character`, `system`, `notes` | Typed in by Nick when starting. These stay out of git |
| `client_settings` | A copy of [`capture/client_settings.json`](../capture/client_settings.json), which mirrors [`client-settings.md`](client-settings.md) |
| `result` | Written at the end: `duration_s`, `frames`, `frames_repeated`, `ticks_skipped`, `latest_grab_ms`, `input_events` by kind, and `client_logs` |

The target is a field of the session, and nothing in the recorder is specific to the Supply Dock.

## client-logs

The game writes plain text logs to `Documents\Frontier\logs\Gamelogs`. At the end of a session the recorder copies the files that changed during it. This needs no change to the client. The chat logs are not copied. Their times are in UTC, to the second.

Neither pilot reads these logs. They are kept for checking the readers.

## For Stage 5

- Decode `video.mkv` with ffmpeg or PyAV. Any recent build reads HEVC 4:4:4.
- Reading from `/mnt/f` is fine for a one-off conversion, at about 230 MB a second for large files. Train from a copy on WSL's own disk.
- The persistent settings are not in `inputs.csv`. The throttle level, for example, is the running count of `e` and `q` presses since a known state. Every session starts with aimed flight on.

## The one-minute test on 2026-11-22

Nick flew for 60 seconds inside the station while the recorder ran.

| Check | Result |
| --- | --- |
| Frames | 601, with none skipped and 1 repeated |
| Gap between frames | 84 to 117 ms, 100 ms on average |
| Latest a frame was taken after its slot | 26 ms |
| Area recorded | The whole 3840 by 2160 monitor, which the borderless game fills |
| Input events | 36 key, 1,830 mouse movement, 1 button, 2 focus |
| Game log | One file copied |

**Inputs against frames.** The first E press was logged at 13.153 s. The frame at 13.197 s shows no change. The frame at 13.297 s shows the throttle gauge starting to fill. So the game's response appears between 44 and 144 ms after the logged press, which is the game's own delay plus at most one frame. The input log and the frames agree to within one frame.

**Fixed after the test.** A mouse button's release was logged without its press when the click was what brought the game to the front. Such a release is now dropped.

**Game speed.** Nick reported that the game felt normal while the recorder ran.

**Still open.** Whether a higher `qp` would cut the file size without making the display harder to read. This waits for the readers (NIC-117).
## The ten-minute test on 2026-11-22

Nick flew approaches to the Supply Dock for 600 seconds. This is the finish line set in NIC-116.

| Check | Result |
| --- | --- |
| Frames | 6,001, with none skipped and 18 repeated |
| Gap between frames | 84 to 120 ms, 100.0 ms on average |
| Latest a frame was taken after its slot | 26 ms |
| Input events | 320 key, 29,994 mouse movement, 4 button, 2 focus |
| Size | 6.04 GB |
| Game log | One file copied, with 11 lines |

**Inputs against frames.** Three inputs were checked by eye against the frames around them.

| Input | Logged at | First frame that shows the response | Delay |
| --- | --- | --- | --- |
| Q pressed, early | 22.551 s | Frame 228, throttle gauge | 144 to 244 ms |
| Mouse moved after 1.5 s of stillness | 269.519 s | Frame 2697, heading tape | 79 to 179 ms |
| Q pressed, late | 595.901 s | Frame 5960, throttle gauge | 0 to 96 ms |

Each range runs from the last frame without the response to the first frame with it. The response never showed before the logged input, and in the late case it showed in the very next frame. So the log and the frames agree to within one frame, and there is no drift over ten minutes. The rest of the delay, up to about two frames, is the game's own, and it varies. Mouse Smoothing is at its centre setting and adds to the delay for mouse movement.

The world model should expect an input to show on screen one to three frames after its row in `inputs.csv`.

**Replay.** The viewer opens the session and draws the inputs on its frames. Checked by saving frames with the overlay. **Not checked**: Nick playing it through in the viewer's window.