# src/pyside6_quasar/core/validation/rule.py
import re
from dataclasses import dataclass
from typing import Callable


@dataclass
class ValidationRule:
    """基础校验规则"""
    validator: Callable[[str], bool]
    message: str

    @staticmethod
    def required(msg="此项为必填项") -> "ValidationRule":
        return ValidationRule(lambda v: bool(v and v.strip()), msg)

    @staticmethod
    def min_length(length: int, msg=None) -> "ValidationRule":
        return ValidationRule(lambda v: len(v) >= length, msg or f"最少输入 {length} 个字符")

    @staticmethod
    def email(msg="邮箱格式不正确") -> "ValidationRule":
        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        return ValidationRule(lambda v: bool(re.match(pattern, v)), msg)

    @staticmethod
    def pattern(regex: str, msg="格式不正确") -> "ValidationRule":
        return ValidationRule(lambda v: bool(re.match(regex, v)), msg)
