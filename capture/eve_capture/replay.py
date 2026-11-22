"""Replay a recorded session with the inputs drawn on the frames.

    uv run eve-replay F:\\eve-flight-recordings\\20261122-190000

Keys:  Space play or pause    . or Right  next frame    , or Left  previous frame
       ] forward 10 s         [ back 10 s               Q or Esc   quit

For each frame, the overlay shows what was held at the frame's time, and what
happened between the previous frame and this one.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np


@dataclass
class FrameInputs:
    held_keys: list[str] = field(default_factory=list)
    held_buttons: list[str] = field(default_factory=list)
    pressed: list[str] = field(default_factory=list)   # went down since the previous frame
    released: list[str] = field(default_factory=list)  # went up since the previous frame
    dx: int = 0
    dy: int = 0
    wheel: int = 0
    in_game: bool = True


class Session:
    def __init__(self, folder: Path):
        self.folder = folder
        self.meta = json.loads((folder / "meta.json").read_text())
        with open(folder / "frames.csv", newline="") as f:
            self.frame_t = [int(r["t_ns"]) for r in csv.DictReader(f)]
        with open(folder / "inputs.csv", newline="") as f:
            self.events = list(csv.DictReader(f))
        for ev in self.events:
            ev["t_ns"] = int(ev["t_ns"])
        self.event_t = [ev["t_ns"] for ev in self.events]
        self.per_frame = self._per_frame()

    def _per_frame(self) -> list[FrameInputs]:
        """Walk the events once and work out the inputs for every frame."""
        out = []
        keys: list[str] = []
        buttons: list[str] = []
        in_game = True
        i = 0
        for t in self.frame_t:
            fi = FrameInputs()
            while i < len(self.events) and self.events[i]["t_ns"] <= t:
                ev = self.events[i]
                i += 1
                kind = ev["kind"]
                if kind == "key" or kind == "button":
                    held = keys if kind == "key" else buttons
                    name = ev["name"]
                    if ev["state"] == "down":
                        if name not in held:
                            held.append(name)
                        fi.pressed.append(name)
                    else:
                        if name in held:
                            held.remove(name)
                        fi.released.append(name)
                elif kind == "move":
                    fi.dx += int(ev["dx"])
                    fi.dy += int(ev["dy"])
                elif kind == "wheel":
                    fi.wheel += int(ev["delta"])
                elif kind == "focus":
                    in_game = ev["state"] == "game"
            fi.held_keys = list(keys)
            fi.held_buttons = list(buttons)
            fi.in_game = in_game
            out.append(fi)
        return out

    def seconds(self, frame: int) -> float:
        return (self.frame_t[frame] - self.frame_t[0]) / 1e9

    def frame_at(self, seconds: float) -> int:
        t = self.frame_t[0] + int(seconds * 1e9)
        return min(len(self.frame_t) - 1, max(0, bisect.bisect_left(self.frame_t, t)))


def draw_overlay(img: np.ndarray, session: Session, n: int) -> np.ndarray:
    """Draw the inputs for frame n in a panel at the top centre of the image."""
    fi = session.per_frame[n]
    h, w = img.shape[:2]
    s = w / 1920  # sizes below are for a 1920-wide image
    font = cv2.FONT_HERSHEY_SIMPLEX
    pw, ph = int(700 * s), int(150 * s)
    x0, y0 = (w - pw) // 2, int(120 * s)
    panel = img[y0:y0 + ph, x0:x0 + pw]
    panel[:] = (panel * 0.25).astype(np.uint8)
    cv2.rectangle(img, (x0, y0), (x0 + pw, y0 + ph), (90, 90, 90), max(1, int(s)))

    def text(line: str, row: int, colour=(255, 255, 255)) -> None:
        cv2.putText(img, line, (x0 + int(14 * s), y0 + int((30 + 28 * row) * s)), font,
                    0.62 * s, colour, max(1, int(1.6 * s)), cv2.LINE_AA)

    gap_ms = (session.frame_t[n] - session.frame_t[n - 1]) / 1e6 if n else 0.0
    text(f"frame {n}/{len(session.frame_t) - 1}   t {session.seconds(n):8.2f} s   "
         f"since last {gap_ms:5.0f} ms" + ("" if fi.in_game else "   [game not in front]"), 0,
         (200, 200, 200))
    held = fi.held_keys + [f"mouse-{b}" for b in fi.held_buttons]
    text("held: " + (" ".join(k.upper() for k in held) or "-"), 1, (80, 220, 255))
    changes = [f"+{k.upper()}" for k in fi.pressed] + [f"-{k.upper()}" for k in fi.released]
    text("this frame: " + (" ".join(changes) or "-"), 2, (120, 255, 120))
    text(f"mouse: dx {fi.dx:+6d}  dy {fi.dy:+6d}" + (f"   wheel {fi.wheel:+d}" if fi.wheel else ""), 3)

    # An arrow for the mouse movement since the previous frame.
    cx, cy = x0 + pw - int(80 * s), y0 + ph // 2
    r = int(55 * s)
    cv2.circle(img, (cx, cy), r, (90, 90, 90), max(1, int(s)))
    if fi.dx or fi.dy:
        mag = (fi.dx ** 2 + fi.dy ** 2) ** 0.5
        scale = min(1.0, mag / 400) * r / mag  # 400 counts in one frame fills the circle
        tip = (int(cx + fi.dx * scale), int(cy + fi.dy * scale))
        cv2.arrowedLine(img, (cx, cy), tip, (255, 255, 255), max(1, int(2 * s)), cv2.LINE_AA,
                        tipLength=0.3)
    return img


class Player:
    def __init__(self, session: Session, width: int):
        self.session = session
        self.cap = cv2.VideoCapture(str(session.folder / session.meta["video"]["file"]))
        if not self.cap.isOpened():
            raise RuntimeError("could not open the video")
        self.width = width
        self.pos = -1  # index of the frame last read

    def read(self, n: int) -> np.ndarray:
        if n != self.pos + 1:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, n)
        ok, img = self.cap.read()
        if not ok:
            raise RuntimeError(f"could not read frame {n}")
        self.pos = n
        if self.width and img.shape[1] != self.width:
            height = round(img.shape[0] * self.width / img.shape[1])
            img = cv2.resize(img, (self.width, height), interpolation=cv2.INTER_AREA)
        return draw_overlay(img, self.session, n)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("session", type=Path)
    p.add_argument("--width", type=int, default=1920, help="display width in pixels (0 = the video's own)")
    p.add_argument("--start", type=float, default=0.0, help="start at this many seconds")
    p.add_argument("--save-frame", type=int, default=None, metavar="N",
                   help="write frame N with its overlay to a PNG and exit")
    p.add_argument("--save-to", type=Path, default=None)
    args = p.parse_args(argv)

    session = Session(args.session)
    player = Player(session, args.width)
    total = len(session.frame_t)

    if args.save_frame is not None:
        out = args.save_to or (args.session / f"replay-frame-{args.save_frame:06d}.png")
        cv2.imwrite(str(out), player.read(args.save_frame))
        print(out)
        return 0

    n = session.frame_at(args.start)
    playing = False
    title = f"eve-replay {session.meta['session_id']}"
    cv2.namedWindow(title, cv2.WINDOW_NORMAL)
    fps = float(session.meta["video"]["nominal_fps"])
    step_10s = int(10 * fps)
    while True:
        cv2.imshow(title, player.read(n))
        key = cv2.waitKeyEx(int(1000 / fps) if playing else 0)
        if cv2.getWindowProperty(title, cv2.WND_PROP_VISIBLE) < 1:
            break
        if key in (ord("q"), ord("Q"), 27):
            break
        if key == ord(" "):
            playing = not playing
        elif key in (ord("."), 0x270000):
            playing = False
            n += 1
        elif key in (ord(","), 0x250000):
            playing = False
            n -= 1
        elif key == ord("]"):
            n += step_10s
        elif key == ord("["):
            n -= step_10s
        elif playing:
            n += 1
        n = max(0, min(total - 1, n))
        if playing and n == total - 1:
            playing = False
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    sys.exit(main())
