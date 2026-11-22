"""Key and mouse logging through the Windows Raw Input API.

Raw Input gives the mouse's own movement counts, which is what the game uses to
turn the camera. The cursor position is no use for that, because the game holds
the cursor in place.

Events are only kept while the game window is in front, so nothing typed into
another program is recorded. This module only listens. It never sends input.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import threading
import time
from typing import Callable

from . import win

user32 = win.user32
kernel32 = win.kernel32

WM_INPUT = 0x00FF
WM_QUIT = 0x0012
RID_INPUT = 0x10000003
RIDEV_INPUTSINK = 0x00000100
RIM_TYPEMOUSE = 0
RIM_TYPEKEYBOARD = 1
HWND_MESSAGE = -3

RI_KEY_BREAK = 0x01
RI_KEY_E0 = 0x02
MOUSE_MOVE_ABSOLUTE = 0x01

BUTTON_FLAGS = [
    (0x0001, "left", "down"),
    (0x0002, "left", "up"),
    (0x0004, "right", "down"),
    (0x0008, "right", "up"),
    (0x0010, "middle", "down"),
    (0x0020, "middle", "up"),
    (0x0040, "x1", "down"),
    (0x0080, "x1", "up"),
    (0x0100, "x2", "down"),
    (0x0200, "x2", "up"),
]
RI_MOUSE_WHEEL = 0x0400
RI_MOUSE_HWHEEL = 0x0800

LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)


class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [
        ("usUsagePage", wt.USHORT),
        ("usUsage", wt.USHORT),
        ("dwFlags", wt.DWORD),
        ("hwndTarget", wt.HWND),
    ]


class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [
        ("dwType", wt.DWORD),
        ("dwSize", wt.DWORD),
        ("hDevice", wt.HANDLE),
        ("wParam", wt.WPARAM),
    ]


# usFlags is followed by two bytes of padding before the button fields.
class RAWMOUSE(ctypes.Structure):
    _fields_ = [
        ("usFlags", wt.USHORT),
        ("_pad", wt.USHORT),
        ("usButtonFlags", wt.USHORT),
        ("usButtonData", wt.USHORT),
        ("ulRawButtons", wt.ULONG),
        ("lLastX", wt.LONG),
        ("lLastY", wt.LONG),
        ("ulExtraInformation", wt.ULONG),
    ]


class RAWKEYBOARD(ctypes.Structure):
    _fields_ = [
        ("MakeCode", wt.USHORT),
        ("Flags", wt.USHORT),
        ("Reserved", wt.USHORT),
        ("VKey", wt.USHORT),
        ("Message", wt.UINT),
        ("ExtraInformation", wt.ULONG),
    ]


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wt.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wt.HINSTANCE),
        ("hIcon", wt.HANDLE),
        ("hCursor", wt.HANDLE),
        ("hbrBackground", wt.HANDLE),
        ("lpszMenuName", wt.LPCWSTR),
        ("lpszClassName", wt.LPCWSTR),
    ]


HEADER_SIZE = ctypes.sizeof(RAWINPUTHEADER)

# Names for the keys the game uses. Anything else is logged as "vk_<number>".
VK_NAMES = {
    0x08: "backspace", 0x09: "tab", 0x0D: "enter", 0x10: "shift", 0x11: "ctrl", 0x12: "alt",
    0x13: "pause", 0x14: "capslock", 0x1B: "esc", 0x20: "space",
    0x21: "pageup", 0x22: "pagedown", 0x23: "end", 0x24: "home",
    0x25: "left", 0x26: "up", 0x27: "right", 0x28: "down", 0x2D: "insert", 0x2E: "delete",
    0x6A: "num*", 0x6B: "num+", 0x6D: "num-", 0x6E: "num.", 0x6F: "num/",
    0xA0: "shift", 0xA1: "shift", 0xA2: "ctrl", 0xA3: "ctrl", 0xA4: "alt", 0xA5: "alt",
    0xBA: ";", 0xBB: "=", 0xBC: ",", 0xBD: "-", 0xBE: ".", 0xBF: "/", 0xC0: "`",
    0xDB: "[", 0xDC: "\\", 0xDD: "]", 0xDE: "'",
}
for _c in range(ord("0"), ord("9") + 1):
    VK_NAMES[_c] = chr(_c)
for _c in range(ord("A"), ord("Z") + 1):
    VK_NAMES[_c] = chr(_c).lower()
for _i in range(10):
    VK_NAMES[0x60 + _i] = f"num{_i}"
for _i in range(1, 25):
    VK_NAMES[0x6F + _i] = f"f{_i}"


def key_name(vkey: int) -> str:
    return VK_NAMES.get(vkey, f"vk_{vkey}")


class RawInputLogger:
    """Listens on its own thread and calls `emit(event)` for each input event.

    An event is a dict with `t_ns` (time.perf_counter_ns), `kind`, and the
    fields for that kind:

      key     name, vkey, scan, state ("down" or "up")
      move    dx, dy   (mouse counts; right and down are positive)
      button  name, state
      wheel   delta    (120 is one notch away from the user)
      focus   state    ("game" or "other")
    """

    def __init__(
        self,
        emit: Callable[[dict], None],
        game_exe: str | None = win.GAME_EXE,
        stop_key: str | None = None,
        on_stop_key: Callable[[], None] | None = None,
    ):
        self._emit = emit
        self._game_exe = game_exe.lower() if game_exe else None
        self._stop_key = stop_key
        self._on_stop_key = on_stop_key
        self._thread = threading.Thread(target=self._run, name="rawinput", daemon=True)
        self._thread_id = 0
        self._ready = threading.Event()
        self._error: Exception | None = None
        self._down: set[tuple[int, int]] = set()
        self._buttons_down: set[str] = set()
        self._in_game: bool | None = None
        self._focus_checked_ns = 0
        self._buf = ctypes.create_string_buffer(256)

    def start(self) -> None:
        self._thread.start()
        self._ready.wait(5)
        if self._error:
            raise self._error

    def stop(self) -> None:
        if self._thread_id:
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        self._thread.join(2)

    # -- focus -------------------------------------------------------------

    def _game_in_front(self, now_ns: int) -> bool:
        if self._game_exe is None:
            return True
        if self._in_game is None or now_ns - self._focus_checked_ns > 50_000_000:
            self._focus_checked_ns = now_ns
            in_game = win.exe_name_of_window(win.foreground_window()) == self._game_exe
            if in_game != self._in_game:
                self._in_game = in_game
                if not in_game:
                    self._release_all(now_ns)
                self._emit({"t_ns": now_ns, "kind": "focus", "state": "game" if in_game else "other"})
        return bool(self._in_game)

    def _release_all(self, now_ns: int) -> None:
        """Log an "up" for everything held, so no key looks stuck after a switch away."""
        for vkey, scan in sorted(self._down):
            self._emit({"t_ns": now_ns, "kind": "key", "name": key_name(vkey), "vkey": vkey,
                        "scan": scan, "state": "up"})
        self._down.clear()
        for name in sorted(self._buttons_down):
            self._emit({"t_ns": now_ns, "kind": "button", "name": name, "state": "up"})
        self._buttons_down.clear()

    # -- message loop ------------------------------------------------------

    def _run(self) -> None:
        try:
            self._thread_id = kernel32.GetCurrentThreadId()
            wndproc = WNDPROC(self._wndproc)
            self._wndproc_ref = wndproc
            kernel32.GetModuleHandleW.restype = wt.HMODULE
            hinst = kernel32.GetModuleHandleW(None)
            cls = WNDCLASSW()
            cls.lpfnWndProc = wndproc
            cls.hInstance = hinst
            cls.lpszClassName = f"EveCaptureRawInput{self._thread_id}"
            if not user32.RegisterClassW(ctypes.byref(cls)):
                raise ctypes.WinError(ctypes.get_last_error())
            user32.CreateWindowExW.restype = wt.HWND
            user32.CreateWindowExW.argtypes = [
                wt.DWORD, wt.LPCWSTR, wt.LPCWSTR, wt.DWORD, ctypes.c_int, ctypes.c_int,
                ctypes.c_int, ctypes.c_int, wt.HWND, wt.HANDLE, wt.HINSTANCE, wt.LPVOID,
            ]
            hwnd = user32.CreateWindowExW(0, cls.lpszClassName, "eve-capture", 0, 0, 0, 0, 0,
                                          wt.HWND(HWND_MESSAGE), None, hinst, None)
            if not hwnd:
                raise ctypes.WinError(ctypes.get_last_error())
            devices = (RAWINPUTDEVICE * 2)(
                RAWINPUTDEVICE(1, 2, RIDEV_INPUTSINK, hwnd),  # mouse
                RAWINPUTDEVICE(1, 6, RIDEV_INPUTSINK, hwnd),  # keyboard
            )
            if not user32.RegisterRawInputDevices(devices, 2, ctypes.sizeof(RAWINPUTDEVICE)):
                raise ctypes.WinError(ctypes.get_last_error())
        except Exception as exc:  # report to the starting thread
            self._error = exc
            self._ready.set()
            return
        self._ready.set()
        msg = wt.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.DispatchMessageW(ctypes.byref(msg))
        user32.DestroyWindow(hwnd)

    def _wndproc(self, hwnd, message, wparam, lparam):
        if message == WM_INPUT:
            now_ns = time.perf_counter_ns()
            try:
                self._handle(lparam, now_ns)
            except Exception:
                pass
        user32.DefWindowProcW.restype = LRESULT
        user32.DefWindowProcW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
        return user32.DefWindowProcW(hwnd, message, wparam, lparam)

    def _handle(self, lparam, now_ns: int) -> None:
        size = wt.UINT(len(self._buf))
        user32.GetRawInputData.argtypes = [wt.HANDLE, wt.UINT, wt.LPVOID,
                                           ctypes.POINTER(wt.UINT), wt.UINT]
        got = user32.GetRawInputData(wt.HANDLE(lparam), RID_INPUT, self._buf,
                                     ctypes.byref(size), HEADER_SIZE)
        if got in (0, 0xFFFFFFFF):
            return
        header = RAWINPUTHEADER.from_buffer(self._buf)
        if header.dwType == RIM_TYPEKEYBOARD:
            kb = RAWKEYBOARD.from_buffer(self._buf, HEADER_SIZE)
            self._on_key(kb, now_ns)
        elif header.dwType == RIM_TYPEMOUSE:
            mouse = RAWMOUSE.from_buffer(self._buf, HEADER_SIZE)
            self._on_mouse(mouse, now_ns)

    def _on_key(self, kb: RAWKEYBOARD, now_ns: int) -> None:
        vkey = kb.VKey
        if vkey in (0, 0xFF):
            return
        is_up = bool(kb.Flags & RI_KEY_BREAK)
        scan = kb.MakeCode | (0xE000 if kb.Flags & RI_KEY_E0 else 0)
        name = key_name(vkey)
        if self._stop_key and name == self._stop_key and not is_up:
            if self._on_stop_key:
                self._on_stop_key()
            return
        if not self._game_in_front(now_ns):
            return
        ident = (vkey, scan)
        if is_up:
            if ident not in self._down:
                return
            self._down.discard(ident)
        else:
            if ident in self._down:  # the keyboard's own repeat while held
                return
            self._down.add(ident)
        self._emit({"t_ns": now_ns, "kind": "key", "name": name, "vkey": vkey, "scan": scan,
                    "state": "up" if is_up else "down"})

    def _on_mouse(self, mouse: RAWMOUSE, now_ns: int) -> None:
        if not self._game_in_front(now_ns):
            return
        flags = mouse.usButtonFlags
        if not (mouse.usFlags & MOUSE_MOVE_ABSOLUTE) and (mouse.lLastX or mouse.lLastY):
            self._emit({"t_ns": now_ns, "kind": "move", "dx": mouse.lLastX, "dy": mouse.lLastY})
        if not flags:
            return
        for bit, name, state in BUTTON_FLAGS:
            if flags & bit:
                if state == "down":
                    self._buttons_down.add(name)
                elif name in self._buttons_down:
                    self._buttons_down.discard(name)
                else:  # the press came before the game was in front
                    continue
                self._emit({"t_ns": now_ns, "kind": "button", "name": name, "state": state})
        if flags & RI_MOUSE_WHEEL:
            delta = ctypes.c_short(mouse.usButtonData).value
            self._emit({"t_ns": now_ns, "kind": "wheel", "delta": delta})
