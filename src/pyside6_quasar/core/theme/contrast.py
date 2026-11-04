# src/pyside6_quasar/core/theme/contrast.py
from .palette import Color


def get_contrast_color(bg_color: str, light: str = Color.WHITE, dark: str = Color.DARK) -> str:
    """根据背景色亮度返回对比文字色 (WCAG 2.0)"""
    bg_color = bg_color.lstrip('#')
    if len(bg_color) == 3:
        bg_color = ''.join([c * 2 for c in bg_color])

    try:
        r = int(bg_color[0:2], 16) / 255.0
        g = int(bg_color[2:4], 16) / 255.0
        b = int(bg_color[4:6], 16) / 255.0
    except (ValueError, IndexError):
        return dark

    def _linearize(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = _linearize(r), _linearize(g), _linearize(b)
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b

    return dark if luminance > 0.179 else light
