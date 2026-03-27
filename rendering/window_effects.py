from __future__ import annotations

import platform


if platform.system() == "Windows":
    import win32api
    import win32con
    import win32gui
else:
    win32api = None
    win32con = None
    win32gui = None


def configure_overlay_window(
    hwnd: int,
    *,
    x: int,
    y: int,
    width: int,
    height: int,
    click_through: bool,
    colorkey_rgb: tuple[int, int, int],
) -> None:
    if win32gui is None or hwnd == 0:
        return

    style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    style |= win32con.WS_EX_LAYERED | win32con.WS_EX_TOPMOST | win32con.WS_EX_TOOLWINDOW
    if click_through:
        style |= win32con.WS_EX_TRANSPARENT
    else:
        style &= ~win32con.WS_EX_TRANSPARENT

    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)
    win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(*colorkey_rgb), 255, win32con.LWA_COLORKEY)
    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_TOPMOST,
        x,
        y,
        width,
        height,
        win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW | win32con.SWP_FRAMECHANGED,
    )


def move_overlay_window(hwnd: int, x: int, y: int, width: int, height: int) -> None:
    if win32gui is None or hwnd == 0:
        return
    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_TOPMOST,
        x,
        y,
        width,
        height,
        win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW,
    )
