# src/pyside6_quasar/core/router/router.py
from typing import Dict, Callable, Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QStackedWidget, QWidget


class Router(QObject):
    """全局路由管理器"""
    routeChanged = Signal(str)

    def __init__(self, stack: QStackedWidget):
        super().__init__()
        self._stack = stack
        self._routes: Dict[str, QWidget] = {}
        self._guards: Dict[str, Callable[[], bool]] = {}
        self._current = ""

    def register(self, path: str, page: QWidget, guard: Optional[Callable[[], bool]] = None):
        """注册路由与守卫"""
        self._routes[path] = page
        self._stack.addWidget(page)
        if guard:
            self._guards[path] = guard

    def push(self, path: str):
        """路由跳转"""
        if path not in self._routes:
            return

        # 路由守卫校验
        guard = self._guards.get(path)
        if guard and not guard():
            return

        self._stack.setCurrentWidget(self._routes[path])
        self._current = path
        self.routeChanged.emit(path)

    @property
    def current_route(self) -> str:
        return self._current
