"""Run the readers over a recorded session and write readings.csv beside it.

    uv run eve-read F:\\eve-flight-recordings\\20261122-190951

Each row is one frame: its time from frames.csv, then a value and a confidence
for every reading. Empty cells are readings that were not found.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from .readers import ClosingSpeed, Readers

FIELDS = ["speed_mps", "speed_marker_y", "throttle", "label_x", "label_y", "range_m", "in_range",
          "nose_dx", "nose_dy", "target_dx", "target_dy", "closing_mps"]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("session", type=Path)
    p.add_argument("--every", type=int, default=1, help="read every Nth frame")
    p.add_argument("--target-template", type=Path, default=None, help="image of the target's name as the label shows it")
    args = p.parse_args(argv)

    meta = json.loads((args.session / "meta.json").read_text())
    w, h = meta["video"]["width"], meta["video"]["height"]
    with open(args.session / "frames.csv", newline="") as f:
        frame_t = [int(r["t_ns"]) for r in csv.DictReader(f)]

    proc = subprocess.Popen(
        ["ffmpeg", "-loglevel", "error", "-i", str(args.session / meta["video"]["file"]),
         "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
        stdout=subprocess.PIPE, bufsize=w * h * 3)
    readers = Readers(args.target_template)
    closing = ClosingSpeed()
    header = ["frame", "t_ns"] + [c for k in FIELDS for c in (k, k + "_conf")]
    took = []
    n = 0
    with open(args.session / "readings.csv", "w", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(header)
        while True:
            buf = proc.stdout.read(w * h * 3)
            if len(buf) < w * h * 3 or n >= len(frame_t):
                break
            if n % args.every == 0:
                im = np.frombuffer(buf, np.uint8).reshape(h, w, 3)
                t = time.perf_counter()
                r = readers.read(im)
                r["closing_mps"] = closing.update(frame_t[n] / 1e9, r["range_m"])
                took.append(time.perf_counter() - t)
                row = [n, frame_t[n]]
                for k in FIELDS:
                    v = r[k]
                    row += ["" if v.value is None else v.value, round(v.confidence, 3)]
                writer.writerow(row)
            n += 1
    proc.kill()
    ms = np.array(took) * 1000
    print(f"Read {len(took)} frames. Time per frame: median {np.median(ms):.0f} ms, "
          f"95th percentile {np.percentile(ms, 95):.0f} ms, slowest {ms.max():.0f} ms.")
    print(args.session / "readings.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
