# quasar/utils/mixin.py
from ...core.theme import Color


class BadgeMixin:
    """
    提供挂载/更新角标能力的 Mixin
    使用方法: my_widget.set_badge("99+", color=Color.NEGATIVE)
    """
    _badge = None

    def set_badge(self, content=None, color=Color.NEGATIVE, is_dot=False, **kwargs):
        from quasar.components.badge import Badge

        if content is None and not is_dot:
            if self._badge:
                self._badge.hide()
                self._badge.deleteLater()
                self._badge = None
            return self

        if self._badge:
            # ★ 修复：调用公共方法，而不是直接操作私有变量和私有方法
            self._badge.set_content(content, is_dot)
            self._badge.show()
        else:
            self._badge = Badge(self, content=content, color=color, is_dot=is_dot, **kwargs)  # type: ignore[arg-type]

        return self
