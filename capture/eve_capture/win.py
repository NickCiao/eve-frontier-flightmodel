"""Small Win32 helpers: DPI awareness, finding the game window, monitors."""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
from dataclasses import dataclass

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

GAME_EXE = "exefile.exe"

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def set_dpi_aware() -> None:
    """Make window and monitor sizes come back in real pixels."""
    try:
        user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except (AttributeError, OSError):
        user32.SetProcessDPIAware()


@dataclass(frozen=True)
class Rect:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    def as_dict(self) -> dict:
        return {"left": self.left, "top": self.top, "width": self.width, "height": self.height}


def exe_name_of_window(hwnd: int) -> str:
    """The exe file name of the process that owns a window, in lower case."""
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(wt.HWND(hwnd), ctypes.byref(pid))
    if not pid.value:
        return ""
    kernel32.OpenProcess.restype = wt.HANDLE
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not handle:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(1024)
        size = wt.DWORD(len(buf))
        ok = kernel32.QueryFullProcessImageNameW(wt.HANDLE(handle), 0, buf, ctypes.byref(size))
        if not ok:
            return ""
        return buf.value.replace("/", "\\").rsplit("\\", 1)[-1].lower()
    finally:
        kernel32.CloseHandle(wt.HANDLE(handle))


def foreground_window() -> int:
    user32.GetForegroundWindow.restype = wt.HWND
    return user32.GetForegroundWindow() or 0


def window_rect(hwnd: int) -> Rect:
    """The client area of a window in screen pixels."""
    rc = wt.RECT()
    user32.GetClientRect(wt.HWND(hwnd), ctypes.byref(rc))
    pt = wt.POINT(0, 0)
    user32.ClientToScreen(wt.HWND(hwnd), ctypes.byref(pt))
    return Rect(pt.x, pt.y, pt.x + rc.right, pt.y + rc.bottom)


def find_game_window(exe: str = GAME_EXE) -> int:
    """The largest visible top-level window owned by the game's exe, or 0."""
    found: list[tuple[int, int]] = []
    proto = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

    def each(hwnd, _lparam):
        if user32.IsWindowVisible(hwnd) and exe_name_of_window(hwnd) == exe.lower():
            r = window_rect(hwnd)
            found.append((r.width * r.height, hwnd))
        return True

    user32.EnumWindows(proto(each), 0)
    if not found:
        return 0
    found.sort(reverse=True)
    return found[0][1]


class _MONITORINFOEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wt.DWORD),
        ("rcMonitor", wt.RECT),
        ("rcWork", wt.RECT),
        ("dwFlags", wt.DWORD),
        ("szDevice", wt.WCHAR * 32),
    ]


def monitor_of_window(hwnd: int) -> tuple[str, Rect]:
    """The device name and pixel bounds of the monitor a window is mostly on."""
    user32.MonitorFromWindow.restype = wt.HANDLE
    mon = user32.MonitorFromWindow(wt.HWND(hwnd), 2)
    return _monitor_info(mon)


def primary_monitor() -> tuple[str, Rect]:
    user32.MonitorFromPoint.restype = wt.HANDLE
    mon = user32.MonitorFromPoint(wt.POINT(0, 0), 1)
    return _monitor_info(mon)


def _monitor_info(mon) -> tuple[str, Rect]:
    info = _MONITORINFOEXW()
    info.cbSize = ctypes.sizeof(info)
    user32.GetMonitorInfoW(wt.HANDLE(mon), ctypes.byref(info))
    r = info.rcMonitor
    return info.szDevice, Rect(r.left, r.top, r.right, r.bottom)
