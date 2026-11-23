"""Readers that turn one frame of the flight display into numbers.

They work on a 3840 by 2160 frame with the client settings in
docs/client-settings.md (UI scaling 200%). Positions below are in those pixels.

Each reading has a value and a confidence from 0 to 1. A value of None means
the reader could not find the thing it reads. The caller adds the frame's time.

The readers are for the hand-written controller and for checking. The world
model is never trained on them.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

ASSETS = Path(__file__).resolve().parent / "assets"

# Throttle gauge: a vertical bar. Throttle fills it upward from the zero mark.
GAUGE_X0, GAUGE_X1 = 975, 981      # columns inside the bar
GAUGE_Y_MAX = 686                  # top of the bar (full throttle)
GAUGE_Y_ZERO = 1385                # just above the zero mark
GAUGE_Y_REV0, GAUGE_Y_REV1 = 1394, 1478  # the reverse part, below zero

# Speed: white text above an orange marker that slides up and down beside the gauge.
MARKER_X0, MARKER_X1 = 1000, 1085
MARKER_Y0, MARKER_Y1 = 640, 1520
SPEED_X0, SPEED_X1 = 985, 1140

# Nose circle: a thin orange ring of fixed size, drawn where the ship's nose points.
NOSE_RADIUS = 100
NOSE_MIN_SCORE = 0.75
SCREEN_CX, SCREEN_CY = 1920, 1080

GLYPH_H, GLYPH_W = 14, 12
DIGITS = "0123456789"


@dataclass
class Reading:
    value: float | str | bool | None
    confidence: float


NOTHING = Reading(None, 0.0)


@dataclass
class Match:
    x: int
    y: int
    char: str
    score: float


class TextMatcher:
    """Finds the display's fixed-size glyphs in a strip of the frame.

    Matching is by normalised correlation, so it does not depend on how bright
    the text is. The strip is a single channel a few rows taller than a glyph.
    """

    def __init__(self):
        data = np.load(ASSETS / "glyphs.npz")
        self.glyphs = {k: data[k].astype(np.float32) for k in data.files}

    def score_map(self, strip: np.ndarray, char: str) -> np.ndarray:
        res = cv2.matchTemplate(strip.astype(np.float32), self.glyphs[char], cv2.TM_CCOEFF_NORMED)
        return np.nan_to_num(res, nan=0.0, posinf=0.0, neginf=0.0)

    def best(self, strip: np.ndarray, char: str) -> tuple[np.ndarray, np.ndarray]:
        """For one character: the best score at every x, and the row it came from."""
        res = self.score_map(strip, char)
        return res.max(axis=0), res.argmax(axis=0)

    def peaks(self, strip: np.ndarray, chars: str, threshold: float) -> list[Match]:
        """Non-overlapping matches, left to right."""
        maps = [self.best(strip, c) for c in chars]
        stack = np.stack([m[0] for m in maps])
        best = stack.max(axis=0).copy()
        which = stack.argmax(axis=0)
        found = []
        while True:
            x = int(best.argmax())
            s = float(best[x])
            if s < threshold:
                break
            k = int(which[x])
            found.append(Match(x, int(maps[k][1][x]), chars[k], s))
            best[max(0, x - 9):x + 10] = 0
        return sorted(found, key=lambda m: m.x)

    def run_ending_at(self, strip: np.ndarray, right: int, threshold: float, max_gap: int) -> list[Match]:
        """The digits that end just left of column `right`, with no gap wider than max_gap."""
        digits = [m for m in self.peaks(strip[:, :right + 2], DIGITS, threshold) if m.x < right - 10]
        run = []
        for m in reversed(digits):
            if right - m.x > max_gap:
                break
            run.append(m)
            right = m.x
        run.reverse()
        return run


class Readers:
    def __init__(self, target_template: Path | None = None):
        self.text = TextMatcher()
        path = target_template or (ASSETS / "target_supply_dock.png")
        full = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if full is None:
            raise FileNotFoundError(path)
        self.target_w = full.shape[1]
        self.target_half = cv2.resize(full, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
        self.in_range_tmpl = cv2.imread(str(ASSETS / "in_range.png"), cv2.IMREAD_GRAYSCALE).astype(np.float32)
        r = NOSE_RADIUS // 2  # the ring is searched for at half size
        ring = np.zeros((2 * r + 5, 2 * r + 5), np.float32)
        cv2.circle(ring, (r + 2, r + 2), r, 1.0, 1)
        self._ring = ring / ring.sum()
        ang = np.linspace(0, 2 * np.pi, 90, endpoint=False)
        self._cos, self._sin = np.cos(ang), np.sin(ang)

    # -- speed ---------------------------------------------------------------

    def speed_marker(self, im: np.ndarray) -> tuple[int | None, float]:
        """The row of the orange marker under the speed text."""
        roi = im[MARKER_Y0:MARKER_Y1, MARKER_X0:MARKER_X1]
        b, g, r = roi[..., 0], roi[..., 1], roi[..., 2]
        mask = (r > 220) & (g > 80) & (g < 170) & (b < 70)
        score = mask.mean(axis=1)
        y = int(score.argmax())
        s = float(score[y])
        # The marker is narrower when it sits on the zero mark, where it covers 0.73 of the width.
        if s < 0.6:
            return None, s
        return y + MARKER_Y0, s

    def speed(self, im: np.ndarray) -> tuple[Reading, int | None]:
        """Speed in metres a second, negative when reversing. Also returns the marker's row.

        The display shows whole metres a second up to 999, then thousands with
        two decimals, for example "1.34K M/S".
        """
        my, _ = self.speed_marker(im)
        if my is None or my < MARKER_Y0 + 30:
            return NOTHING, None
        strip = im[my - 23:my - 3, SPEED_X0:SPEED_X1, 1]
        unit, _ = self.text.best(strip, "M")
        ux = int(unit.argmax())
        conf = float(unit[ux])
        if conf < 0.7:
            return NOTHING, my
        right = ux
        thousands = False
        if ux >= 30:
            k, _ = self.text.best(strip[:, ux - 26:ux - 6], "K")
            if k.max() > 0.75:
                thousands = True
                right = ux - 26 + int(k.argmax())
        run = self.text.run_ending_at(strip, right, 0.7, 26)
        if not run or len(run) > 4 or (thousands and len(run) != 3):
            return NOTHING, my
        value = int("".join(m.char for m in run))
        if thousands:
            value *= 10  # "1.34K" is read as 134, and means 1340
        conf = min(conf, min(m.score for m in run))
        if self._minus_before(strip, run[0]):
            value = -value
        elif self._clutter_before(strip, run[0]):
            conf *= 0.4  # something bright may be hiding a minus sign or a digit
        return Reading(float(value), conf), my

    @staticmethod
    def _clutter_before(strip: np.ndarray, first: Match) -> bool:
        """Bright pixels just left of the first digit that are not a minus sign."""
        x0 = max(0, first.x - 16)
        patch = strip[first.y:first.y + GLYPH_H, x0:first.x].astype(np.float32)
        level = float(strip[first.y:first.y + GLYPH_H, first.x:first.x + GLYPH_W].max())
        return bool(patch.size and (patch > 0.6 * level).mean() > 0.15)

    def _minus_before(self, strip: np.ndarray, first: Match) -> bool:
        """A minus sign sits in the 16 columns left of the first digit, at the same height."""
        if first.x < 16:
            return False
        patch = strip[first.y:first.y + GLYPH_H, first.x - 16:first.x].astype(np.float32)
        if patch.shape != (GLYPH_H, 16) or patch.std() < 8:
            return False
        s = cv2.matchTemplate(patch, self.text.glyphs["minus"], cv2.TM_CCOEFF_NORMED)[0, 0]
        return bool(s > 0.75)

    # -- throttle ------------------------------------------------------------

    def throttle(self, im: np.ndarray) -> Reading:
        """Throttle from -1 (full reverse) to 1 (full forward), from the gauge's fill."""
        col = im[:, GAUGE_X0:GAUGE_X1].astype(np.float32).mean(axis=1)
        b, g, r = col[:, 0], col[:, 1], col[:, 2]
        fill = (r > 215) & (g > 85) & (g < 175) & (b < 70)
        # forward: walk up from zero, allowing the short dividers between sections
        top = GAUGE_Y_ZERO
        gap = 0
        y = GAUGE_Y_ZERO - 1
        while y >= GAUGE_Y_MAX:
            if fill[y]:
                top = y
                gap = 0
            else:
                gap += 1
                if gap > 8:
                    break
            y -= 1
        forward = (GAUGE_Y_ZERO - top) / (GAUGE_Y_ZERO - GAUGE_Y_MAX)
        reverse = float(fill[GAUGE_Y_REV0:GAUGE_Y_REV1].mean())
        # The bar's outline is an orange line at x = 986. If it is missing, the display is hidden.
        edge = im[GAUGE_Y_MAX:GAUGE_Y_ZERO, 986:988].astype(np.float32).mean(axis=(0, 1))
        shown = edge[2] > 90 and edge[2] > edge[1] * 1.5 and edge[2] > edge[0] * 1.5
        if not shown:
            return NOTHING
        if reverse > 0.05 and forward < 0.02:
            return Reading(-reverse, 0.9)
        return Reading(float(forward), 0.9)

    # -- target label --------------------------------------------------------

    def target(self, im: np.ndarray, half: np.ndarray | None = None) -> dict[str, Reading]:
        """The target's label: where it is on screen, and the range line above its name.

        label_x and label_y are the centre of the target's name, in pixels.
        range_m is the distance left to the edge of docking range, in metres.
        It is 0 when the line says IN RANGE. It is None when the line is hidden
        or something is drawn over it.
        """
        if half is None:
            half = cv2.resize(im, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
        res = cv2.matchTemplate(cv2.cvtColor(half, cv2.COLOR_BGR2GRAY), self.target_half, cv2.TM_CCOEFF_NORMED)
        _, score, _, loc = cv2.minMaxLoc(res)
        out = {"label_x": NOTHING, "label_y": NOTHING, "range_m": NOTHING, "in_range": NOTHING}
        if score < 0.7:
            return out
        x, y = loc[0] * 2, loc[1] * 2
        cx = x + self.target_w // 2
        out["label_x"] = Reading(float(cx), float(score))
        out["label_y"] = Reading(float(y + 17), float(score))
        x0 = max(0, cx - 260)
        strip_bgr = im[max(0, y - 38):max(0, y - 10), x0:cx + 260]
        if strip_bgr.shape[0] < GLYPH_H + 2 or strip_bgr.shape[1] < 120:
            return out
        out["range_m"], out["in_range"] = self._range_line(strip_bgr[..., 1], strip_bgr, cx - x0)
        return out

    def _range_line(self, strip: np.ndarray, strip_bgr: np.ndarray, centre: int) -> tuple[Reading, Reading]:
        m, _ = self.text.best(strip, "M")
        xs = np.where(m > 0.72)[0]
        if len(xs) == 0:
            if strip.shape[1] >= self.in_range_tmpl.shape[1]:
                s = cv2.matchTemplate(strip.astype(np.float32), self.in_range_tmpl, cv2.TM_CCOEFF_NORMED)
                # The words are centred over the name, so only look there.
                s = np.nan_to_num(s).max(axis=0)
                want = centre - self.in_range_tmpl.shape[1] // 2
                s = float(s[max(0, want - 10):want + 11].max()) if 0 <= want < len(s) else 0.0
                # IN RANGE is drawn in orange. White or grey text of a similar shape is something else.
                blue, green, red = (strip_bgr[..., i].astype(np.int16) for i in range(3))
                orange = int(((red > 190) & (green > 60) & (green < 175) & (blue < 90)).sum())
                if s > 0.7 and orange > 300:  # the words alone are about 550 orange pixels
                    return Reading(0.0, s), Reading(True, s)
            return NOTHING, NOTHING
        # the unit's M is the right-most strong one
        ux = int(xs[-1])
        lo = max(0, ux - 3)
        ux = lo + int(m[lo:ux + 4].argmax())
        conf = float(m[ux])
        right = ux
        is_km = False
        if ux >= 18:
            k, _ = self.text.best(strip[:, ux - 18:ux - 9 + GLYPH_W], "K")
            if k.max() > 0.65:
                is_km = True
                right = ux - 18 + int(k.argmax())
        not_in_range = Reading(False, conf)
        # Letters and the bracket also match digits weakly, so the bar is high
        # here and the gap rule stops at the bracket.
        run = self.text.run_ending_at(strip, right, 0.8, 24)
        if not run or len(run) > 4 or (is_km and len(run) < 2):
            return NOTHING, not_in_range
        conf = min(conf, min(d.score for d in run))
        # The opening bracket should sit just left of the first digit. If something
        # else is there, a digit may be hidden, so the reading is not trusted.
        if not self._bracket_before(strip, run[0]):
            conf *= 0.3
        value = float(int("".join(d.char for d in run)))
        if is_km:
            value *= 100.0  # "6.5 KM" is read as 65
        return Reading(value, conf), not_in_range

    @staticmethod
    def _bracket_before(strip: np.ndarray, first: Match) -> bool:
        """A thin tall stroke 9 to 17 columns left of the first digit, with clear space beside it."""
        if first.x < 20:
            return False
        patch = strip[first.y:first.y + GLYPH_H, first.x - 20:first.x - 1].astype(np.float32)
        level = float(strip[first.y:first.y + GLYPH_H, first.x:first.x + GLYPH_W].max())
        if level < 60:
            return False
        cols = (patch > 0.5 * level).sum(axis=0)  # 19 columns
        tall = np.where(cols >= 10)[0]
        if len(tall) == 0 or len(tall) > 4:
            return False
        # nothing else bright between the bracket and the digit
        between = cols[tall.max() + 4:]
        return bool(tall.max() <= 11 and (between <= 2).all())

    # -- nose circle ---------------------------------------------------------

    @staticmethod
    def _thin_bright(channel: np.ndarray) -> np.ndarray:
        """How much brighter each pixel is than its surroundings, from 0 to 1."""
        local = cv2.blur(channel, (9, 9))
        return np.clip((channel - local) / (local + 20.0), 0, 0.4) / 0.4

    def nose(self, half: np.ndarray) -> dict[str, Reading]:
        """Where the ship's nose points, as pixels right of and below the screen centre.

        The game draws the nose circle only while the camera is turned away from
        the ship's heading. When no circle is found the offsets are None.
        `half` is the frame at half size, in colour.
        """
        half = half.astype(np.float32)
        ridge = np.maximum(self._thin_bright(half[..., 2]), self._thin_bright(half[..., 1]))
        res = cv2.matchTemplate(ridge, self._ring, cv2.TM_CCORR)
        r = NOSE_RADIUS // 2
        h, w = ridge.shape
        best_score, best_xy = 0.0, None
        for _ in range(6):
            _, _, _, loc = cv2.minMaxLoc(res)
            cx, cy = loc[0] + r + 2, loc[1] + r + 2
            cv2.circle(res, loc, 12, 0, -1)
            if abs(cx - SCREEN_CX // 2) < 5 and abs(cy - SCREEN_CY // 2) < 5:
                continue  # the centre circle, which marks the camera

            def on_ring(radius, src):
                xs = np.clip((cx + radius * self._cos).round().astype(int), 0, w - 1)
                ys = np.clip((cy + radius * self._sin).round().astype(int), 0, h - 1)
                return src[ys, xs]

            on = np.maximum(on_ring(r, ridge), np.maximum(on_ring(r - 1, ridge), on_ring(r + 1, ridge)))
            off = 0.5 * (on_ring(r - 5, ridge) + on_ring(r + 5, ridge))
            hit = (on > 0.25) & (on > off + 0.2)
            score = float(hit.mean())  # how much of the way round the ring is lit
            if hit.sum() > 5:
                b, g, red = on_ring(r, half)[hit].mean(axis=0)
                orange = red > 50 and 0.25 * red < g < 0.7 * red and b < 0.5 * red
                if not orange:
                    score *= 0.5
            if score > best_score:
                best_score, best_xy = score, (cx * 2, cy * 2)
        if best_xy is None or best_score < NOSE_MIN_SCORE:
            return {"nose_dx": NOTHING, "nose_dy": NOTHING}
        return {"nose_dx": Reading(float(best_xy[0] - SCREEN_CX), best_score),
                "nose_dy": Reading(float(best_xy[1] - SCREEN_CY), best_score)}

    # -- everything ----------------------------------------------------------
    def read(self, im: np.ndarray) -> dict[str, Reading]:
        speed, marker_y = self.speed(im)
        out = {
            "speed_mps": speed,
            "speed_marker_y": Reading(float(marker_y), 1.0) if marker_y is not None else NOTHING,
            "throttle": self.throttle(im),
        }
        half = cv2.resize(im, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
        out.update(self.target(im, half))
        out.update(self.nose(half))
        # Direction to the target from the nose, in pixels. With no nose circle
        # on screen the nose is taken to be at the centre, with less confidence.
        lx, ly, nx, ny = out["label_x"], out["label_y"], out["nose_dx"], out["nose_dy"]
        if lx.value is None:
            out["target_dx"] = out["target_dy"] = NOTHING
        elif nx.value is not None:
            conf = min(lx.confidence, nx.confidence)
            out["target_dx"] = Reading(lx.value - SCREEN_CX - nx.value, conf)
            out["target_dy"] = Reading(ly.value - SCREEN_CY - ny.value, conf)
        else:
            out["target_dx"] = Reading(lx.value - SCREEN_CX, 0.5 * lx.confidence)
            out["target_dy"] = Reading(ly.value - SCREEN_CY, 0.5 * lx.confidence)
        return out


class ClosingSpeed:
    """Closing speed toward the target, in metres a second, from the range readings over time.

    The range line steps in 100 m beyond 1 km, so this is coarse out there. It
    compares the newest trusted range with the one about a second older.
    """

    def __init__(self, window_s: float = 1.0, min_confidence: float = 0.6):
        self.window_s = window_s
        self.min_confidence = min_confidence
        self._history: list[tuple[float, float]] = []

    def update(self, t_s: float, range_m: Reading) -> Reading:
        if range_m.value is None or range_m.confidence < self.min_confidence:
            return NOTHING
        self._history.append((t_s, float(range_m.value)))
        self._history = [h for h in self._history if t_s - h[0] <= 3 * self.window_s]
        older = [h for h in self._history if t_s - h[0] >= self.window_s]
        if not older:
            return NOTHING
        t0, r0 = older[-1]
        return Reading((r0 - float(range_m.value)) / (t_s - t0), range_m.confidence)
