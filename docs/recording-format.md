# Recording format

Format version 1, written on 2026-11-22 for NIC-116. The recorder is in [`capture/`](../capture/README.md). It was tested on 2026-11-22 on the desktop only. **Not checked**: a recording of the game itself, and whether inputs line up with frames within one frame.

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
| Size | About 9 MB for 5 seconds of a still desktop. **Not checked**: the size for game footage |

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
