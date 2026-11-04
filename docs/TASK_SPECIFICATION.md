这份《任务说明书》是为你量身定制的**工程交接文档（Handover Document）**。它的核心作用是建立一套“上下文锚点”，无论你在何时、何地开启新会话，只要把这份文档发给 AI，它就能瞬间理解你的架构、进度、约定和下一步计划，实现**无缝续写**。

建议将其保存为 `docs/TASK_SPECIFICATION.md`，作为项目的最高纲领。

---

# 📘 PySide6 旗舰版 Quasar 框架设计任务说明书

## 0. 文档元信息
*   **项目名称**：`pyside6-quasar`
*   **项目定位**：对标 Vue Quasar 的工业级桌面应用框架。纯 `QPainter` 渲染，零 QSS，支持全局主题切换，专为“铝脑智助”等数据密集型 SaaS 打造。
*   **Python 版本**：`>=3.10`
*   **PySide6 版本**：`>=6.6`
*   **当前状态**：v0.1.0-alpha（L0-L2 核心重构中）
*   **文档更新日期**：2024-05-20

---

## 1. 核心架构与目录规范 (L0 - L4)

框架严格采用 `src`-layout，并遵循单向依赖的 5 层架构，**严禁反向依赖**。

| 层级 | 目录路径 | 职责说明 | 依赖关系 |
| :--- | :--- | :--- | :--- |
| **L4 模板层** | `src/pyside6_quasar/templates/` | 业务骨架（如 LoginPage, DashboardPage） | 依赖 L0-L3 |
| **L3 数据层** | `src/pyside6_quasar/components/data/` | 复杂数据组件（Table, Select），使用 Delegate 模式 | 依赖 L0-L2 |
| **L2 容器层** | `src/pyside6_quasar/components/containers/` | 布局容器（Card, Tabs, Dialog, Drawer） | 依赖 L0-L1 |
| **L1 基础层** | `src/pyside6_quasar/components/primitives/` | 纯自绘组件（Button, Input, Checkbox, Switch, Avatar, Badge, Progress） | 仅依赖 L0 |
| **L0 基建层** | `src/pyside6_quasar/core/` | 主题、路由、状态、表单校验、基础基类 | 无 UI 依赖 |

---

## 2. 绝对底线：核心编程规范

后续开发**必须**严格遵守以下规则，否则会引发 C++ 底层崩溃或架构腐化。

### 2.1 相对导入规范（极易踩坑）
*   **`pyside6_quasar/__init__.py`**：`from .core.theme import theme_manager`
*   **`core/__init__.py`**：`from .theme import theme_manager`（**1个点，同级**）
*   **`core/base/widget.py`**：`from ...theme import theme_manager`（**3个点，祖父级**）
*   **`components/primitives/xxx.py`**：`from ...core.base import QBaseWidget`（**3个点**）
*   *严禁出现 `from ...core.base` 写在 `core/__init__.py` 中，会触发 `beyond top-level package` 错误。*

### 2.2 多重继承与基类规范
彻底废弃旧版的 `ThemedWidget`。根据组件类型，严格选择以下两种继承范式：

**范式 A：纯自绘组件（如 Card, Switch, Checkbox, Progress）**
```python
from ...core.base import QBaseWidget

class MyWidget(QBaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent) # 自动完成 QWidget 初始化、主题监听、DPR 计算
```
*   **禁止**手动调用 `self.setup_theme()`。
*   **禁止**重写 `focusInEvent`/`focusOutEvent` 时忘记调用 `super().focusInEvent(event)`。

**范式 B：基于原生控件的组件（如 Button, Dialog）**
```python
from PySide6.QtWidgets import QPushButton
from ...core.base import QuasarWidgetMixin

class Button(QPushButton, QuasarWidgetMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_quasar() # 必须手动挂载
```

### 2.3 主题响应规范
*   所有颜色**严禁硬编码**，必须从 `theme_manager.get_color("key")` 动态拉取。
*   可用 Token：`background`, `surface`, `border`, `text_primary`, `text_secondary`, `hover`, `disabled`, `primary`。
*   当主题切换时，`QBaseWidget` 会自动调用 `self.update()`。如果组件内部有原生子控件（如 `QLineEdit`），必须重写 `_on_theme_changed` 并刷新其 QSS：
    ```python
    def _on_theme_changed(self, mode: ThemeMode):
        self._update_internal_qss()
        super()._on_theme_changed(mode)
    ```

### 2.4 内存与动画生命周期
*   对于挂在全局或父窗口的悬浮窗（如 Tooltip, Toast），`QPropertyAnimation` **必须**在每次触发时重新创建并指定 `parent`，防止底层 C++ 对象被提前 GC 回收（引发 `libshiboken already deleted` 崩溃）。
*   高 DPI 适配统一使用 `self.dpr` 属性（定义在 `QBaseWidget` 中），**禁止**在绘制代码中自行调用 `QApplication.primaryScreen().devicePixelRatio()`。

---

## 3. 当前进度全景 (State of the Union)

### ✅ 已彻底重构完成（遵循全新基类与规范）
1.  **`__init__.py`**：实现了基于 PEP 562 的懒加载机制，包含完整的路由图与版本预测。
2.  **核心基建 (`core/`)**：
    *   `theme/`：`ThemeManager`、语义化 `Color` 调色板、`get_contrast_color`。
    *   `base/`：`QBaseWidget`、`QuasarWidgetMixin`。
    *   `mixins/`：`BadgeMixin`。
    *   `router/`、`validation/`：基础逻辑已跑通。
3.  **L1 基础组件**：`Avatar`, `Badge`, `Button`, `Input`。
4.  **L2 容器组件**：`Dialog`。

### 🚧 待重构的组件（代码已有，但存在旧版 `ThemedWidget` 残留）
以下组件的**业务逻辑**（动画、事件、尺寸计算）已非常完善，但在新架构下，**需要将它们迁移到 `QBaseWidget` 基类**，并修复相对导入路径。
1.  `Checkbox` （需改为 `QBaseWidget`，删除 `setup_theme()`）
2.  `Switch` （需改为 `QBaseWidget`，修复原代码中横杠颜色的无效语句）
3.  `LineProgress` / `CircleProgress` （需改为 `QBaseWidget`）
4.  `Card` / `CardSection` / `CardActions` / `CardMedia` （需改为 `QBaseWidget`）
5.  `Tabs` / `TabItem` （需改为 `QBaseWidget`）
6.  `Toast` （需改为 `QBaseWidget`）
7.  `Tooltip` （需改为 `QBaseWidget`）

---

## 4. 核心代码资产索引

当你（AI/开发者）需要修改或参考代码时，请直接定位：

*   **基类定义**：`src/pyside6_quasar/core/base/widget.py`
*   **主题系统**：`src/pyside6_quasar/core/theme/manager.py`
*   **防崩溃动画范式**：`src/pyside6_quasar/components/feedback/tooltip.py` 中的 `_apply_transition_show` 方法。
*   **Delegate 表格预期范式**：尚未创建，将在 L3 层实现。使用 `QAbstractTableModel` + `QStyledItemDelegate`，禁止在 `paintEvent` 中直接遍历绘制表格行。

---

## 5. 下一步行动清单 (Action Items)

1.  **阶段目标 1：完成剩余 7 个组件的 `QBaseWidget` 迁移**。
    *   严格按照第 2.2 节的范式 A 进行修改。
    *   确保内部的原生控件（如 `Card` 的关闭按钮）的颜色随主题更新。
2.  **阶段目标 2：创建 L3 数据组件 `Table`**。
    *   落盘至 `src/pyside6_quasar/components/data/table/`。
    *   包含 `model.py`, `delegate.py`, `view.py`。
    *   支持行悬浮高亮、斑马纹、自定义单元格组件嵌套。
3.  **阶段目标 3：提供企业级演示程序 (Gallery)**。
    *   整合所有组件，提供深浅主题一键切换。

---

## 6. 新会话启动指令 (Prompt Template)

**当你开启新的 AI 会话时，请直接复制以下文本发送：**

> 你好，我们正在开发 `pyside6-quasar` 企业级框架。请仔细阅读以下任务说明书，这是我们的架构上下文与当前进度：
> 
> （此处粘贴上文第 1 节至第 5 节内容）
> 
> **当前任务指令**：
> 现在我们继续推进【阶段目标 1】。请帮我重构 `Checkbox` 组件。以下是旧版代码（基于 ThemedWidget 的多重继承），请按照规范将其迁移为 `QBaseWidget` 范式，并检查是否有遗留的原生 QSS 需要动态更新。
> 
> （此处粘贴旧版 Checkbox 代码）