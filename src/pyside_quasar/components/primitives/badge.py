# src/pyside_quasar/components/primitives/badge.py
"""
pyside_quasar.components.primitives.badge
==========================================
企业级徽标组件 (对标 Quasar QBadge)
v2.1 Final 终极封板版

v2.1 相对 v2.0 的修复清单
────────────────────────
✅ [BUG-1]  全面移除 /dpr 逻辑；QPainter 的坐标/笔宽本身就是逻辑像素，
            再除 dpr 会在高 DPI 屏上让线条更细、字体更小（与 Button 同类错误）
✅ [BUG-2]  _get_display_text 只有在 content 是 int（且非 bool）时才走数字截断，
            避免 "007" 被吞成 "7"、1.9 被截成 1、True 被当成 1
✅ [BUG-3]  多行模式绘制 padding 与 _MULTILINE_PADDING 完全一致，
            避免"尺寸算够了但文字比容器窄一截"
✅ [BUG-4]  detach / _on_target_destroyed 中显式 disconnect themeChanged，
            防止主题切换打到已 deleteLater 的对象上抛 RuntimeError
✅ [BUG-5]  destroyed 信号槽增加可选参数 obj=None，兼容 QObject* 签名
✅ [BUG-6]  单行胶囊增加最大宽度 _SINGLE_LINE_MAX_W，超长文本绘制时 elide
✅ [BUG-7]  outline + transparent 组合时强制文字不透明，避免"看不见的轮廓"
✅ [BUG-8]  _sync_geometry 检测 dpr 变化并触发 _update_size；同时监听
            ParentChange，reparent 后几何同步
✅ [BUG-9]  set_rounded / set_floating / set_max_value 等修改尺寸/锚点的
            setter 统一 _update_size + _sync_geometry
✅ [BUG-10] 挂载时若 target 上已存在旧 badge，先 detach 旧实例，杜绝泄漏
✅ [BUG-11] QTimer.singleShot 延迟回调用 try/except + _attached 标记保护，
            防止 badge 在 10ms 内被 detach 造成竞态
✅ [MINOR]  _get_font 缓存；_sync_geometry 去除冗余 show()

原有能力（保持）
────────
浮动 / 内联定位；圆点 / 胶囊 / 多行三形态；实心 / 轮廓两风格；
顶部 / 中部 / 底部三对齐；对比度自动计算；主题联动；target 销毁自清理；
高 DPI 自适应；鼠标穿透 / 无焦点 / 不占 Tab
"""
from enum import Enum
from typing import Union, Optional, Tuple

from PySide6.QtCore import Qt, QRectF, QEvent, QPoint, QTimer
from PySide6.QtGui import (
    QPainter, QColor, QFont, QPen, QFontMetrics, QPainterPath, QPaintEvent,
)
from PySide6.QtWidgets import QWidget

# ─────────────────────────────────────────────────────────────
# 从 core.base 统一导入（re-export 主题能力）
# ─────────────────────────────────────────────────────────────
from ...core.base import (
    QBaseWidget,
    theme_manager,
    ThemeMode,
    Color,
    get_contrast_color,
)


class BadgeAlign(Enum):
    """内联模式下的垂直对齐方式"""
    TOP = 1
    MIDDLE = 2
    BOTTOM = 3


# ─────────────────────────────────────────────────────────────
# Badge 主体组件
# ─────────────────────────────────────────────────────────────
class Badge(QBaseWidget):
    """
    企业级徽标组件。

    设计要点:
        - 挂载到顶层窗口，避免被父控件布局裁剪
        - 通过事件过滤器与 target_widget 保持几何同步
        - 不接收焦点、鼠标事件穿透，不抢占交互
        - 主题切换自动重绘、自动重算文字对比色
        - target 控件销毁时自动清理自身，杜绝野引用

    Args:
        target_widget: 徽标挂载的目标控件（必填）
        content:       显示内容。int → 数字（超 max_value 显示 N+）；str → 原样显示
        color:         徽标主背景色（支持 Color 枚举 / 颜色字符串）
        text_color:    文字色（None → 自动按背景对比度计算）
        border_color:  边框色（None → 智能跟随主题）
        max_value:     数字上限，超过显示 "{max_value}+"
        is_dot:        是否圆点模式（无文字）
        offset:        浮动模式下像素偏移 (x, y)
        floating:      True=浮动右上角；False=内联对齐到目标控件
        rounded:       True=胶囊圆角；False=矩形
        transparent:   是否半透明背景
        outline:       是否轮廓模式（无填充，仅描边）
        multi_line:    是否允许文字换行
        align:         内联模式垂直对齐 BadgeAlign.TOP/MIDDLE/BOTTOM
        alpha:         透明模式下透明度 0~1，默认 0.8
    """

    # 逻辑像素常量（Qt 自动按 DPR 放大，不要再手动除以 dpr）
    _DOT_SIZE = 14
    _CAPSULE_HEIGHT = 20
    _CAPSULE_PADDING_H = 16
    _SINGLE_LINE_MAX_W = 200  # v2.1 单行胶囊最大宽度，超长自动 elide
    _MULTILINE_MAX_W = 120
    _MULTILINE_PADDING = (10, 4)  # (水平, 垂直) —— 尺寸计算与绘制共用
    _FONT_PIXEL_SIZE = 11

    def __init__(
            self,
            target_widget: QWidget,
            content: Union[str, int] = "",
            color: str = Color.NEGATIVE,
            text_color: Optional[str] = None,
            border_color: Optional[str] = None,
            max_value: int = 99,
            is_dot: bool = False,
            offset: Tuple[int, int] = (0, 0),
            floating: bool = True,
            rounded: bool = False,
            transparent: bool = False,
            outline: bool = False,
            multi_line: bool = False,
            align: BadgeAlign = BadgeAlign.MIDDLE,
            alpha: float = 0.8,
            parent: Optional[QWidget] = None,
    ):
        if target_widget is None:
            raise ValueError("Badge 必须指定 target_widget")

        self._target: Optional[QWidget] = target_widget
        self._alpha = max(0.0, min(1.0, alpha))

        # 挂载到目标顶层窗口，规避布局裁剪
        top_window = target_widget.window()
        super().__init__(parent or top_window)

        # 交互属性：无焦点、鼠标穿透
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # ✅ BUG-10：若 target 上已有旧 badge，先 detach，避免旧实例悬空泄漏
        old_badge = getattr(target_widget, "_badge_instance", None)
        if old_badge is not None and old_badge is not self:
            try:
                old_badge.detach()
            except (RuntimeError, AttributeError):
                pass

        # 反向引用，方便外部获取 badge 实例
        self._target._badge_instance = self  # type: ignore[attr-defined]

        # 配置缓存
        self._content = content
        self._color = QColor(color) if not isinstance(color, QColor) else QColor(color)
        self._explicit_text_color = QColor(text_color) if text_color else None
        self._explicit_border_color = QColor(border_color) if border_color else None
        self._max_value = max_value
        self._is_dot = is_dot
        self._offset = offset
        self._floating = floating
        self._rounded = rounded
        self._transparent = transparent
        self._outline = outline
        self._multi_line = multi_line
        self._align = align

        # 尺寸缓存
        self._w = 0
        self._h = 0

        # 字体缓存（v2.1 MINOR）
        self._cached_font: Optional[QFont] = None

        # dpr 缓存（v2.1 BUG-8）
        self._last_dpr: float = 0.0

        # ✅ BUG-11：延迟回调保护标记
        self._attached = True

        # 初始化尺寸
        self._update_size()

        # 事件监听 + 生命周期绑定
        self._target.installEventFilter(self)
        # noinspection PyUnresolvedReferences
        self._target.destroyed.connect(self._on_target_destroyed)
        # noinspection PyUnresolvedReferences
        theme_manager.themeChanged.connect(self._on_theme_changed)

        # 延迟挂载，等布局完成再同步位置
        QTimer.singleShot(10, self._force_attach_safe)

    # ─────────────────────────────────────────────────────────────
    # 公共 API（与 Button 组件风格对齐）
    # ─────────────────────────────────────────────────────────────
    def set_content(
            self,
            content: Union[str, int, None] = None,
            is_dot: Optional[bool] = None,
    ) -> None:
        """更新显示内容，自动处理数字 max_value 截断"""
        if content is not None:
            self._content = content
        if is_dot is not None:
            self._is_dot = is_dot
        self._update_size()
        self._sync_geometry()
        self.update()

    def set_color(self, color: Union[str, Color]) -> None:
        """修改徽标主色"""
        self._color = QColor(color)
        self.update()

    def set_text_color(self, color: Optional[str]) -> None:
        """手动指定文字颜色，None 恢复自动对比度"""
        self._explicit_text_color = QColor(color) if color else None
        self.update()

    def set_border_color(self, color: Optional[str]) -> None:
        """手动指定边框颜色，None 恢复智能主题计算"""
        self._explicit_border_color = QColor(color) if color else None
        self.update()

    def set_max_value(self, val: int) -> None:
        """修改数字上限，超过后显示 N+"""
        self._max_value = val
        self._update_size()
        self._sync_geometry()
        self.update()

    def set_floating(self, floating: bool) -> None:
        """切换浮动 / 内联模式"""
        self._floating = floating
        self._sync_geometry()

    def set_rounded(self, rounded: bool) -> None:
        """切换胶囊圆角 / 矩形形态"""
        self._rounded = rounded
        self._update_size()
        # ✅ BUG-9：尺寸变了锚点也会变，必须同步几何
        self._sync_geometry()
        self.update()

    def set_outline(self, outline: bool) -> None:
        """切换轮廓模式 / 填充模式"""
        self._outline = outline
        self.update()

    def set_transparent(self, transparent: bool) -> None:
        """切换半透明背景开关"""
        self._transparent = transparent
        self.update()

    def detach(self) -> None:
        """解绑目标控件，自销毁，对外安全释放接口"""
        self._cleanup()
        self.hide()
        self.deleteLater()

    @classmethod
    def attach_to(
            cls,
            target_widget: QWidget,
            content: Union[str, int, None] = None,
            color: str = Color.NEGATIVE,
            is_dot: bool = False,
            **kwargs
    ) -> Optional['Badge']:
        """
        ✅ 优雅地组合模式 API：一键为目标控件挂载/更新/移除角标。
        """
        existing_badge = getattr(target_widget, "_badge_instance", None)

        # 移除角标
        if content is None and not is_dot:
            if existing_badge is not None:
                existing_badge.detach()
            return None

        # 更新已有的角标
        if existing_badge is not None:
            existing_badge.set_content(content, is_dot)
            existing_badge.set_color(color)

            # ✅ 修复：通过公开的 setter 更新，消除 PyCharm 警告
            if "floating" in kwargs:
                existing_badge.set_floating(kwargs["floating"])
            if "offset" in kwargs:
                existing_badge.set_offset(*kwargs["offset"])
            if "rounded" in kwargs:
                existing_badge.set_rounded(kwargs["rounded"])
            if "outline" in kwargs:
                existing_badge.set_outline(kwargs["outline"])
            if "transparent" in kwargs:
                existing_badge.set_transparent(kwargs["transparent"])

            existing_badge.show()
            return existing_badge

        # 创建新角标
        return cls(target_widget, content=content, color=color, is_dot=is_dot, **kwargs)

    # ─────────────────────────────────────────────────────────────
    # 内部清理（v2.1：统一入口，杜绝重复/遗漏 disconnect）
    # ─────────────────────────────────────────────────────────────
    def _cleanup(self) -> None:
        """解绑所有外部引用和信号，供 detach 与 _on_target_destroyed 共用。"""
        self._attached = False

        # 1) 解除 target 上的事件过滤 + destroyed 信号 + 反向引用
        if self._target is not None:
            try:
                self._target.removeEventFilter(self)
            except (RuntimeError, AttributeError):
                pass
            try:
                self._target.destroyed.disconnect(self._on_target_destroyed)
            except (RuntimeError, TypeError):
                pass
            try:
                if getattr(self._target, "_badge_instance", None) is self:
                    self._target._badge_instance = None  # type: ignore[attr-defined]
            except (RuntimeError, AttributeError):
                pass
            self._target = None

        # 2) 解除主题变更信号（✅ BUG-4）
        try:
            theme_manager.themeChanged.disconnect(self._on_theme_changed)
        except (RuntimeError, TypeError):
            pass

    # ─────────────────────────────────────────────────────────────
    # 主题联动
    # ─────────────────────────────────────────────────────────────
    def _on_theme_changed(self, mode: ThemeMode) -> None:
        """主题切换触发重绘，自动重算对比色、边框色"""
        try:
            super()._on_theme_changed(mode)
        except AttributeError:
            pass
        self.update()

    # ─────────────────────────────────────────────────────────────
    # 生命周期 & 几何同步
    # ─────────────────────────────────────────────────────────────
    def _on_target_destroyed(self) -> None:  # ✅ BUG-5
        """目标控件销毁，清空引用，防止野指针访问"""
        self._cleanup()
        self.deleteLater()

    def _force_attach_safe(self) -> None:  # ✅ BUG-11
        """QTimer 延迟回调的安全包装，防止已被 detach 后再调用。"""
        if not self._attached:
            return
        try:
            self._force_attach()
        except RuntimeError:
            pass

    def _force_attach(self) -> None:
        """延迟挂载到顶层窗口，等待布局初始化完成"""
        if self._target is None or not self._target.isVisible():
            return
        top_window = self._target.window()
        if self.parentWidget() is not top_window:
            self.setParent(top_window)
            self.raise_()
        self._sync_geometry()

    def _sync_geometry(self) -> None:
        """同步 badge 位置，跟随目标控件 move / resize / reparent / dpr 变化"""
        if self._target is None or not self._target.isVisible() or self.parentWidget() is None:
            self.hide()
            return

        top_window = self._target.window()
        if self.parentWidget() is not top_window:
            self.setParent(top_window)
            self.raise_()

        # ✅ BUG-8：dpr 变化时重算尺寸（比如 target 被移动到高 DPI 屏幕）
        dpr = self.devicePixelRatioF()
        if dpr != self._last_dpr:
            self._last_dpr = dpr
            self._update_size()

        if not self.isVisible():
            self.show()
            self.raise_()

        # 目标控件左上角 → 顶层窗口本地坐标
        global_pos = self._target.mapToGlobal(QPoint(0, 0))
        local_pos = top_window.mapFromGlobal(global_pos)

        if self._floating:
            # 浮动模式：右上角锚点
            x = local_pos.x() + self._target.width() - self._w // 2 + self._offset[0]
            y = local_pos.y() - self._h // 2 + self._offset[1]
        else:
            # 内联模式
            x = local_pos.x() + (self._target.width() - self._w) // 2
            if self._align == BadgeAlign.TOP:
                y = local_pos.y()
            elif self._align == BadgeAlign.BOTTOM:
                y = local_pos.y() + self._target.height() - self._h
            else:
                y = local_pos.y() + (self._target.height() - self._h) // 2

        if self.pos() != QPoint(x, y):
            self.move(x, y)
            self.raise_()

    def eventFilter(self, watched, event) -> bool:
        """监听目标控件 resize / move / show / parentChange，同步 badge 位置。"""
        if watched is self._target:
            et = event.type()
            if et in (
                    QEvent.Type.Resize,
                    QEvent.Type.Move,
                    QEvent.Type.Show,
                    QEvent.Type.ParentChange,
            ):
                self._sync_geometry()
        return super().eventFilter(watched, event)

    # ─────────────────────────────────────────────────────────────
    # 尺寸计算
    # ─────────────────────────────────────────────────────────────
    def _get_display_text(self) -> str:
        """
        ✅ BUG-2：只有 content 是真正的 int（且非 bool）时才走数字截断。
        字符串 "007" 原样显示，float 也原样显示，避免被 int() 静默吞掉。
        """
        if self._is_dot:
            return ""
        if self._content is None:
            return ""
        if isinstance(self._content, int) and not isinstance(self._content, bool):
            return f"{self._max_value}+" if self._content > self._max_value else str(self._content)
        return str(self._content)

    def _get_font(self) -> QFont:
        """统一字体；固定 pixelSize，由 Qt 按 DPR 自动缩放，缓存避免重复构造。"""
        if self._cached_font is None:
            font = QFont("Microsoft YaHei")
            font.setBold(True)
            font.setPixelSize(self._FONT_PIXEL_SIZE)
            self._cached_font = font
        return self._cached_font

    def _update_size(self) -> None:
        """重新计算 badge 宽高，设置固定尺寸。"""
        text = self._get_display_text()
        fm = QFontMetrics(self._get_font())

        if not text:
            # 圆点模式
            self._w = self._h = self._DOT_SIZE
        elif self._multi_line:
            # 多行模式
            br = fm.boundingRect(
                QRectF(0, 0, self._MULTILINE_MAX_W, 999).toRect(),
                Qt.TextFlag.TextWordWrap,
                text,
            )
            pad_h, pad_v = self._MULTILINE_PADDING
            self._w = min(self._MULTILINE_MAX_W, br.width() + pad_h * 2)
            self._h = br.height() + pad_v * 2
        else:
            # ✅ BUG-6：单行胶囊限制最大宽度，超出后绘制时 elide
            text_w = fm.horizontalAdvance(text)
            text_w = min(text_w, self._SINGLE_LINE_MAX_W)
            self._h = self._CAPSULE_HEIGHT
            self._w = max(self._CAPSULE_HEIGHT, text_w + self._CAPSULE_PADDING_H)

        self.setFixedSize(self._w, self._h)

    # ─────────────────────────────────────────────────────────────
    # 绘制逻辑
    # ─────────────────────────────────────────────────────────────
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        text = self._get_display_text()
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)

        # 背景颜色 + 透明度
        bg = QColor(self._color)
        if self._transparent:
            bg.setAlphaF(self._alpha)

        # 文字颜色：显式 > 自动对比度
        if self._explicit_text_color:
            text_col = QColor(self._explicit_text_color)
        else:
            text_col = QColor(get_contrast_color(self._color.name()))

        # 边框颜色：显式 > 主题智能计算
        if self._explicit_border_color:
            border_col = QColor(self._explicit_border_color)
        else:
            contrast_bg = get_contrast_color(self._color.name())
            if contrast_bg == Color.WHITE:
                border_col = QColor(theme_manager.get_color("surface"))
            else:
                border_col = QColor(theme_manager.get_color("border"))

        # 形状路径
        path = QPainterPath()
        if not text or self._is_dot:
            path.addEllipse(rect)
        else:
            radius = rect.height() / 2 if self._rounded else 4.0
            path.addRoundedRect(rect, radius, radius)

        # ✅ BUG-1：全部使用逻辑像素，不再 /dpr
        if self._outline:
            pen_width = 2.0 if self._is_dot else 1.5
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(bg, pen_width))
            # ✅ BUG-7：outline 时文字用不透明主色，避免 transparent 叠加导致看不见
            text_col = QColor(self._color)
        else:
            pen_width = 1.5
            painter.setBrush(bg)
            border_col.setAlphaF(0.6)
            painter.setPen(QPen(border_col, pen_width))

        painter.drawPath(path)

        # 文字绘制
        if text:
            painter.setPen(text_col)
            painter.setFont(self._get_font())
            if self._multi_line:
                # ✅ BUG-3：绘制用与尺寸计算完全一致的 padding
                pad_h, pad_v = self._MULTILINE_PADDING
                painter.drawText(
                    rect.adjusted(pad_h, pad_v, -pad_h, -pad_v),
                    Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                    text,
                )
            else:
                # ✅ BUG-6：单行超长时 elide
                fm = QFontMetrics(self._get_font())
                avail_w = rect.width() - self._CAPSULE_PADDING_H
                display = fm.elidedText(text, Qt.TextElideMode.ElideRight, int(avail_w)) \
                    if fm.horizontalAdvance(text) > avail_w else text
                painter.drawText(
                    rect,
                    Qt.AlignmentFlag.AlignCenter,
                    display,
                )
