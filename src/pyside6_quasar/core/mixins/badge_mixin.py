# src/pyside6_quasar/core/mixins/badge_mixin.py
from ...core.theme.palette import Color


class BadgeMixin:
    """提供挂载/更新角标能力的 Mixin"""
    _badge = None

    def set_badge(self, content=None, color=Color.NEGATIVE, is_dot=False, **kwargs):
        from ...components.primitives.badge import Badge
        if content is None and not is_dot:
            if self._badge:
                self._badge.hide()
                self._badge.deleteLater()
                self._badge = None
            return self

        if self._badge:
            self._badge.set_content(content, is_dot)
            self._badge.show()
        else:
            self._badge = Badge(self, content=content, color=color, is_dot=is_dot, **kwargs)
        return self
