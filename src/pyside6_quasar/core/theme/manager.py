# src/pyside6_quasar/core/theme/manager.py
from enum import Enum
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication


class ThemeMode(Enum):
    LIGHT = 1
    DARK = 2


class ThemeManager(QObject):
    """全局主题管理器 (单例)"""
    _instance = None
    themeChanged = Signal(ThemeMode)

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ThemeManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        super().__init__()
        if not hasattr(self, '_initialized'):
            self._mode = ThemeMode.DARK  # 默认深色

            # 语义化 Design Tokens
            self._tokens = {
                ThemeMode.DARK: {
                    "background": "#121212",  # 页面底色
                    "surface": "#1E1E1E",  # 卡片底色
                    "border": "#37474F",  # 边框色
                    "text_primary": "#FFFFFF",  # 主文字
                    "text_secondary": "#90A4AE",  # 副文字
                    "hover": "rgba(255,255,255,0.08)",  # 悬浮背景
                    "primary": "#1976D2"
                },
                ThemeMode.LIGHT: {
                    "background": "#F5F5F5",
                    "surface": "#FFFFFF",
                    "border": "#E0E0E0",
                    "text_primary": "#212121",
                    "text_secondary": "#757575",
                    "hover": "rgba(0,0,0,0.05)",
                    "primary": "#1976D2"
                }
            }
            self._initialized = True

    @property
    def mode(self) -> ThemeMode:
        return self._mode

    def is_dark(self) -> bool:
        return self._mode == ThemeMode.DARK

    def get_color(self, key: str) -> str:
        """获取当前主题的语义化颜色"""
        return self._tokens[self._mode].get(key, "#FFFFFF")

    def toggle(self):
        self.set_mode(ThemeMode.LIGHT if self._mode == ThemeMode.DARK else ThemeMode.DARK)

    def set_mode(self, mode: ThemeMode):
        if self._mode != mode:
            self._mode = mode
            self._apply_global_qss()
            self.themeChanged.emit(self._mode)

    def _apply_global_qss(self):
        """统一应用到原生基础控件和滚动条"""
        app = QApplication.instance()
        if not app: return

        bg = self.get_color("background")
        border = self.get_color("border")
        primary = self.get_color("primary")
        text = self.get_color("text_primary")

        app.setStyleSheet(f"""
            QMainWindow, QDialog {{ background-color: {bg}; }}
            QLabel {{ color: {text}; }}
            QScrollBar:vertical {{
                background: transparent; width: 8px; margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {border}; min-height: 20px; border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {primary}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)


# 导出单例
theme_manager = ThemeManager()
