# tests/test_button.py
"""
Button v2.0 单元测试
覆盖：枚举解析、颜色逻辑、焦点属性、ellipsis开关、尺寸解析、状态切换
"""
import pytest
from PySide6.QtWidgets import QApplication
from pyside_quasar.components.primitives.button import (
    Button, ButtonVariant, ButtonShape, ButtonSize, _parse_size
)
from pyside_quasar.core.base import Color

app = QApplication.instance() or QApplication([])

def test_parse_size():
    assert _parse_size("xs") == 20
    assert _parse_size(ButtonSize.LG) == 40
    assert _parse_size(66) == 66
    assert _parse_size("99px") == 99

def test_button_create():
    btn = Button("Test")
    assert btn.text() == "Test"
    assert btn.variant == ButtonVariant.FILLED
    assert btn.ellipsis is True
    assert btn.focus_ring_enabled is True
    assert btn.keep_focus_ring_on_click is False

def test_focus_property():
    btn = Button("focus test")
    btn.focus_ring_width = 3
    assert btn.focus_ring_width == 3
    btn.focus_color = "#ff0000"
    assert btn.focus_color == "#ff0000"
    btn.focus_ring_enabled = False
    assert btn.focus_ring_enabled is False
    btn.keep_focus_ring_on_click = True
    assert btn.keep_focus_ring_on_click is True

def test_ellipsis_switch():
    btn = Button("超长文本测试，超长文本测试，超长文本测试")
    assert btn.ellipsis is True
    btn.ellipsis = False
    assert btn.ellipsis is False

def test_variant_shape_parse():
    btn = Button("test", variant="outline", shape="round")
    assert btn._variant == ButtonVariant.OUTLINE
    assert btn._shape == ButtonShape.ROUND

def test_loading_api():
    btn = Button("load")
    btn.set_loading(True)
    assert btn._is_loading is True
    btn.set_loading(False)
    assert btn._is_loading is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
