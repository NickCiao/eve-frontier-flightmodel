"""Record the game window, the key and mouse input, and the game's own log.

    uv run eve-record --target "Supply Dock"

Stop with the stop key (F10 unless changed) or Ctrl-C in the terminal.
The session layout is described in docs/recording-format.md.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

from . import FORMAT_VERSION, win
from .rawinput import RawInputLogger

DEFAULT_ROOT = Path(os.environ.get("EVE_RECORDINGS_DIR", r"F:\eve-flight-recordings"))
GAMELOG_DIR = Path.home() / "Documents" / "Frontier" / "logs" / "Gamelogs"
SETTINGS_FILE = Path(__file__).resolve().parent.parent / "client_settings.json"

INPUT_FIELDS = ["t_ns", "kind", "name", "state", "dx", "dy", "delta", "vkey", "scan"]


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", type=Path, default=DEFAULT_ROOT, help="folder that holds the sessions")
    p.add_argument("--fps", type=float, default=10.0)
    p.add_argument("--duration", type=float, default=0.0, help="stop after this many seconds (0 = until stopped)")
    p.add_argument("--stop-key", default="f10", help="key that stops the recording, by the names in rawinput.py")
    p.add_argument("--qp", type=int, default=18, help="video quality; lower is better and larger")
    p.add_argument("--target", default="Supply Dock", help="the approach target for this session")
    p.add_argument("--arrival", default='label shows "IN RANGE" and speed under 10 m/s')
    p.add_argument("--distance-source", default='the "OUT OF RANGE" line above the target\'s name')
    p.add_argument("--pilot", default="human", help="who flies: human, controller, or world-model")
    p.add_argument("--character", default="", help="character name; stays in the session folder")
    p.add_argument("--system", default="", help="solar system; stays in the session folder")
    p.add_argument("--notes", default="")
    p.add_argument("--no-input", action="store_true", help="test mode: do not log keys or the mouse")
    p.add_argument("--any-window", action="store_true",
                   help="test mode: record the primary monitor and keep input from every program")
    return p.parse_args(argv)


class VideoWriter:
    """Feeds raw BGRA frames to ffmpeg, which encodes them with the NVIDIA encoder."""

    def __init__(self, path: Path, width: int, height: int, fps: float, qp: int):
        self.cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{width}x{height}",
            "-r", f"{fps:g}", "-i", "-",
            "-c:v", "hevc_nvenc", "-preset", "p5", "-tune", "hq",
            "-rc", "constqp", "-qp", str(qp),
            "-profile:v", "rext", "-pix_fmt", "yuv444p",
            "-g", str(max(1, round(fps))), "-bf", "0",
            str(path),
        ]
        self.proc = subprocess.Popen(self.cmd, stdin=subprocess.PIPE)
        self.queue: queue.Queue = queue.Queue(maxsize=8)
        self.error: Exception | None = None
        self.thread = threading.Thread(target=self._run, name="video", daemon=True)
        self.thread.start()

    def _run(self) -> None:
        try:
            while True:
                frame = self.queue.get()
                if frame is None:
                    break
                self.proc.stdin.write(frame.data)
        except Exception as exc:
            self.error = exc

    def write(self, frame) -> None:
        if self.error:
            raise self.error
        self.queue.put(frame)

    def close(self) -> int:
        self.queue.put(None)
        self.thread.join(60)
        try:
            self.proc.stdin.close()
        except OSError:
            pass
        return self.proc.wait(120)


def open_camera(monitor: win.Rect, is_primary: bool):
    """A dxcam camera on the monitor with these bounds."""
    import dxcam

    if is_primary:
        cam = dxcam.create(output_color="BGRA")
        if cam is not None and (cam.width, cam.height) == (monitor.width, monitor.height):
            return cam
    for idx in range(8):
        try:
            cam = dxcam.create(output_idx=idx, output_color="BGRA")
        except Exception:
            break
        if cam is not None and (cam.width, cam.height) == (monitor.width, monitor.height):
            return cam
    raise RuntimeError(f"no capture output matches the {monitor.width}x{monitor.height} monitor")


def copy_gamelogs(session: Path, started: float) -> list[str]:
    """Copy the game's own log files that were written during the session."""
    copied = []
    if not GAMELOG_DIR.is_dir():
        return copied
    dest = session / "client-logs"
    for f in GAMELOG_DIR.glob("*.txt"):
        if f.stat().st_mtime >= started - 1:
            dest.mkdir(exist_ok=True)
            shutil.copy2(f, dest / f.name)
            copied.append(f.name)
    return sorted(copied)


def main(argv=None) -> int:
    args = parse_args(argv)
    win.set_dpi_aware()

    if args.any_window:
        hwnd = 0
        device, monitor = win.primary_monitor()
        region = monitor
        game_exe = None
    else:
        hwnd = win.find_game_window()
        if not hwnd:
            print("The game window was not found. Start the game first, or use --any-window to test.")
            return 2
        device, monitor = win.monitor_of_window(hwnd)
        region = win.window_rect(hwnd)
        game_exe = win.GAME_EXE
        if region != monitor:
            print(f"Warning: the game window ({region.width}x{region.height} at {region.left},{region.top}) "
                  f"does not fill its monitor ({monitor.width}x{monitor.height}). Recording the window's area.")

    _, primary = win.primary_monitor()
    cam = open_camera(monitor, monitor == primary)
    # The region to grab, in the monitor's own coordinates.
    grab_region = (region.left - monitor.left, region.top - monitor.top,
                   region.right - monitor.left, region.bottom - monitor.top)
    width, height = region.width, region.height

    now = dt.datetime.now().astimezone()
    session_id = now.strftime("%Y%m%d-%H%M%S")
    session = args.out / session_id
    session.mkdir(parents=True, exist_ok=False)

    stop = threading.Event()
    events: queue.SimpleQueue = queue.SimpleQueue()
    logger = RawInputLogger(events.put, game_exe=game_exe, stop_key=args.stop_key, on_stop_key=stop.set)

    video = VideoWriter(session / "video.mkv", width, height, args.fps, args.qp)
    frames_file = open(session / "frames.csv", "w", newline="")
    frames_csv = csv.writer(frames_file)
    frames_csv.writerow(["frame", "t_ns", "new"])
    inputs_file = open(session / "inputs.csv", "w", newline="")
    inputs_csv = csv.DictWriter(inputs_file, fieldnames=INPUT_FIELDS, restval="")
    inputs_csv.writeheader()

    counts = {"key": 0, "move": 0, "button": 0, "wheel": 0, "focus": 0}

    def drain_inputs() -> None:
        while True:
            try:
                ev = events.get_nowait()
            except queue.Empty:
                return
            counts[ev["kind"]] = counts.get(ev["kind"], 0) + 1
            inputs_csv.writerow(ev)

    settings = json.loads(SETTINGS_FILE.read_text()) if SETTINGS_FILE.exists() else {}
    settings.pop("_comment", None)

    wall_start = time.time()
    t0_ns = time.perf_counter_ns()
    meta = {
        "format_version": FORMAT_VERSION,
        "session_id": session_id,
        "started_local": now.isoformat(timespec="seconds"),
        "started_utc": dt.datetime.fromtimestamp(wall_start, dt.timezone.utc).isoformat(timespec="milliseconds"),
        "clock": {
            "note": "Every t_ns is time.perf_counter_ns() on the recording PC. "
                    "t0_ns is that clock at the moment started_utc was read.",
            "t0_ns": t0_ns,
            "started_unix": wall_start,
        },
        "video": {
            "file": "video.mkv", "codec": "hevc (hevc_nvenc, constqp)", "qp": args.qp,
            "pixel_format": "yuv444p", "width": width, "height": height,
            "nominal_fps": args.fps, "keyframe_every": max(1, round(args.fps)),
            "note": "Row n of frames.csv is frame n of the video. Use frames.csv for times.",
        },
        "capture": {
            "method": "DXGI Desktop Duplication (dxcam)",
            "monitor": device, "monitor_bounds": monitor.as_dict(), "region": region.as_dict(),
            "game_window_found": bool(hwnd), "any_window_test": args.any_window,
        },
        "inputs": {
            "file": "inputs.csv", "method": "Windows Raw Input",
            "only_while_game_in_front": game_exe is not None,
            "stop_key": args.stop_key, "logged": not args.no_input,
        },
        "task": {
            "target": args.target, "arrival": args.arrival,
            "distance_source": args.distance_source, "pilot": args.pilot,
        },
        "character": args.character,
        "system": args.system,
        "notes": args.notes,
        "client_settings": settings,
    }
    (session / "meta.json").write_text(json.dumps(meta, indent=2))

    if not args.no_input:
        logger.start()
    print(f"Recording to {session}")
    print(f"Stop with {args.stop_key.upper()} or Ctrl-C.")

    period_ns = round(1e9 / args.fps)
    frame_no = 0
    repeated = 0
    skipped_ticks = 0
    late_ns_max = 0
    last = None
    tick = 0
    start_ns = time.perf_counter_ns()
    try:
        while not stop.is_set():
            due = start_ns + tick * period_ns
            wait = (due - time.perf_counter_ns()) / 1e9
            if wait > 0:
                # Sleep in short steps so input is written out and the stop key is seen.
                time.sleep(min(wait, 0.02))
                drain_inputs()
                continue
            frame = cam.grab(region=grab_region)
            t_ns = time.perf_counter_ns()
            is_new = frame is not None
            if frame is None:
                frame = last
            if frame is None:  # nothing on screen has changed since the camera opened
                time.sleep(0.005)
                continue
            last = frame
            video.write(frame)
            frames_csv.writerow([frame_no, t_ns, int(is_new)])
            frame_no += 1
            repeated += 0 if is_new else 1
            late_ns_max = max(late_ns_max, t_ns - due)
            # If the loop fell behind by whole ticks, skip them. The times in frames.csv stay true.
            behind = (time.perf_counter_ns() - due) // period_ns
            if behind >= 1:
                skipped_ticks += int(behind)
                tick += int(behind)
            tick += 1
            drain_inputs()
            if args.duration and (t_ns - start_ns) / 1e9 >= args.duration:
                break
    except KeyboardInterrupt:
        pass
    finally:
        end_ns = time.perf_counter_ns()
        if not args.no_input:
            logger.stop()
        drain_inputs()
        frames_file.close()
        inputs_file.close()
        print("Finishing the video...")
        ffmpeg_code = video.close()
        del cam

    meta["result"] = {
        "duration_s": round((end_ns - start_ns) / 1e9, 3),
        "frames": frame_no,
        "frames_repeated": repeated,
        "ticks_skipped": skipped_ticks,
        "latest_grab_ms": round(late_ns_max / 1e6, 2),
        "input_events": counts,
        "ffmpeg_exit_code": ffmpeg_code,
        "client_logs": copy_gamelogs(session, wall_start),
    }
    (session / "meta.json").write_text(json.dumps(meta, indent=2))
    r = meta["result"]
    print(f"Saved {r['frames']} frames over {r['duration_s']} s "
          f"({r['frames_repeated']} repeated, {r['ticks_skipped']} ticks skipped). "
          f"Input events: {sum(counts.values())}.")
    print(f"Replay with: uv run eve-replay {session}")
    return 0 if ffmpeg_code == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
