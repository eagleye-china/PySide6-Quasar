# utils/window_utils.py
import ctypes
import logging
import sys

from PySide6.QtWidgets import QWidget

logger = logging.getLogger(__name__)

# Windows API 常量
DWMWA_USE_IMMERSIVE_DARK_MODE_OLD = 19  # Win10 1809 - 1909
DWMWA_USE_IMMERSIVE_DARK_MODE_NEW = 20  # Win10 2004+ / Win11
DWMWA_BORDER_COLOR = 34  # Win11 专有：窗口边框颜色
DWMWA_CAPTION_COLOR = 35  # Win11 专有：标题栏背景色


def _set_dwm_attribute(hwnd: int, attribute: int, value: int) -> bool:
    """底层封装：安全地设置 DWM 属性"""
    if sys.platform != "win32" or not hwnd:
        return False
    try:
        # 显式声明参数类型，防止 64 位下的指针截断
        dwmapi = ctypes.windll.dwmapi
        dwmapi.DwmSetWindowAttribute.argtypes = [
            ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32
        ]
        dwmapi.DwmSetWindowAttribute.restype = ctypes.c_long

        res = dwmapi.DwmSetWindowAttribute(
            ctypes.c_void_p(hwnd),
            attribute,
            ctypes.byref(ctypes.c_int(value)),
            ctypes.sizeof(ctypes.c_int)
        )
        return res == 0  # S_OK == 0
    except Exception as e:
        logger.debug(f"[WARN] 调用 DWM API 失败: {e}")
        return False


def enable_dark_title_bar(window: QWidget, enable: bool = True):
    """
    强制将 Windows 操作系统的原生标题栏变为深色/浅色模式。
    支持 Windows 10 20H1 及以上，以及 Windows 11。

    :param window: PySide6 窗口对象
    :param enable: True 为深色，False 为浅色（跟随系统）
    """
    if sys.platform != "win32":
        return

    # ✅ 解决时序问题：使用 QTimer 延迟执行，确保窗口底层真正创建完毕
    from PySide6.QtCore import QTimer

    def _apply():
        try:
            hwnd = int(window.winId())
            if not hwnd:
                return

            dark_value = 1 if enable else 0

            # 尝试 Win10 2004+ / Win11 属性 (20)
            if not _set_dwm_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE_NEW, dark_value):
                # 回退到 Win10 1809 - 1909 属性 (19)
                _set_dwm_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE_OLD, dark_value)

            # 可选：如果是 Win11，可以顺便修复最大化时的白边（设置为深色）
            # if enable:
            #     _set_dwm_attribute(hwnd, DWMWA_BORDER_COLOR, 0x00000000) # 纯黑边框

        except Exception as e:
            logger.debug(f"[WARN] 无法开启深色标题栏: {e}")

    # 延迟 10 毫秒执行，让窗口完成底层句柄分配
    QTimer.singleShot(10, _apply)
