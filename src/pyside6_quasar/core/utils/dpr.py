# src/pyside6_quasar/core/utils/dpr.py
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget


def get_dpr(widget: QWidget = None) -> float:
    """
    获取当前屏幕的 Device Pixel Ratio。
    如果传入了 widget，优先获取该 widget 所在屏幕的 DPR，保证多显示器环境下的清晰度。
    """
    if widget and widget.window().windowHandle():
        return widget.window().windowHandle().devicePixelRatio()

    screen = QGuiApplication.primaryScreen()
    return screen.devicePixelRatio() if screen else 1.0
