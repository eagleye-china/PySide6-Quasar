# src/pyside_quasar/core/validation/form.py
from typing import Dict, List

from .rule import ValidationRule


class FormValidator:
    """表单聚合校验器"""

    def __init__(self):
        self._fields: Dict[str, dict] = {}

    def add_field(self, field_id: str, widget, rules: List[ValidationRule]):
        self._fields[field_id] = {
            "widget": widget,
            "rules": rules
        }

    def validate(self) -> bool:
        """校验所有字段，返回是否全部通过，并自动触发 Input 的错误状态"""
        is_valid = True
        for field_id, cfg in self._fields.items():
            widget = cfg["widget"]
            value = widget.get_text() if hasattr(widget, "get_text") else ""

            # 清空错误
            if hasattr(widget, "clear_error"):
                widget.clear_error()

            for rule in cfg["rules"]:
                if not rule.validator(value):
                    if hasattr(widget, "set_error"):
                        widget.set_error(rule.message)
                    is_valid = False
                    break  # 只要触发一条错误即跳出当前字段校验
        return is_valid
