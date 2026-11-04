pyside6-quasar/
│
├── src/                                    # ★ src-layout：所有源码都在这里
│   └── pyside6_quasar/                     # 包名（下划线）
│       ├── __init__.py                     # 顶层 API 导出（唯一出口）
│       ├── py.typed                        # PEP 561 类型标记
│       │
│       ├── core/                           # ═══ L0 核心基建层 ═══
│       │   ├── __init__.py
│       │   ├── theme/                      # 主题系统
│       │   │   ├── __init__.py
│       │   │   ├── manager.py              # ThemeManager 单例
│       │   │   ├── tokens.py               # Design Tokens（语义化）
│       │   │   ├── palette.py              # 品牌色/调色板
│       │   │   └── contrast.py             # 对比度算法
│       │   ├── base/                       # 组件基类
│       │   │   ├── __init__.py
│       │   │   ├── mixin.py                # QuasarWidgetMixin
│       │   │   └── widget.py               # QBaseWidget
│       │   ├── router/                     # 路由系统
│       │   │   ├── __init__.py
│       │   │   ├── router.py
│       │   │   ├── guard.py                # 路由守卫
│       │   │   └── transition.py           # 页面切换动画
│       │   ├── state/                      # 全局状态
│       │   │   ├── __init__.py
│       │   │   ├── store.py                # AppStore（Pinia 风格）
│       │   │   └── slices/                 # 状态切片
│       │   │       ├── user_slice.py
│       │   │       └── app_slice.py
│       │   ├── events/                     # 事件总线
│       │   │   ├── __init__.py
│       │   │   └── bus.py
│       │   ├── validation/                 # 表单校验
│       │   │   ├── __init__.py
│       │   │   ├── rule.py                 # ValidationRule
│       │   │   ├── validator.py            # 单字段校验器
│       │   │   └── form.py                 # FormValidator
│       │   ├── i18n/                       # 国际化
│       │   │   ├── __init__.py
│       │   │   ├── translator.py
│       │   │   └── locales/
│       │   │       ├── zh_CN.json
│       │   │       └── en_US.json
│       │   └── utils/                      # 通用工具
│       │       ├── __init__.py
│       │       ├── dpr.py                  # 高分屏适配
│       │       ├── painter.py              # QPainter 辅助
│       │       ├── animation.py            # 动画工厂
│       │       ├── color.py                # 颜色转换
│       │       └── geometry.py             # 几何计算
│       │
│       ├── components/                     # ═══ L1-L3 组件层 ═══
│       │   ├── __init__.py
│       │   │
│       │   ├── primitives/                 # L1：纯 QPainter 自绘
│       │   │   ├── __init__.py
│       │   │   ├── button/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── button.py           # Button
│       │   │   │   ├── variant.py          # ButtonVariant
│       │   │   │   └── ripple.py           # 水波纹效果
│       │   │   ├── input/
│       │   │   ├── checkbox.py
│       │   │   ├── switch.py
│       │   │   ├── radio.py
│       │   │   ├── slider.py
│       │   │   ├── avatar.py
│       │   │   ├── badge.py
│       │   │   ├── chip.py
│       │   │   └── progress/
│       │   │       ├── line_progress.py
│       │   │       └── circle_progress.py
│       │   │
│       │   ├── containers/                 # L2：容器布局
│       │   │   ├── __init__.py
│       │   │   ├── card/
│       │   │   ├── tabs/
│       │   │   ├── dialog/
│       │   │   ├── drawer/
│       │   │   ├── collapse/
│       │   │   └── grid/
│       │   │
│       │   ├── data/                       # L3：数据视图（Delegate 模式）
│       │   │   ├── __init__.py
│       │   │   ├── table/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── model.py            # QAbstractTableModel
│       │   │   │   ├── delegate.py         # QStyledItemDelegate
│       │   │   │   └── view.py             # QTableView 封装
│       │   │   ├── list/
│       │   │   ├── tree/
│       │   │   └── select/
│       │   │
│       │   └── feedback/                   # 反馈组件
│       │       ├── __init__.py
│       │       ├── toast/
│       │       │   ├── __init__.py
│       │       │   ├── toast.py
│       │       │   ├── position.py
│       │       │   └── registry.py         # 分组注册表
│       │       ├── tooltip.py
│       │       └── notification.py
│       │
│       ├── layouts/                        # 布局骨架
│       │   ├── __init__.py
│       │   ├── main_layout.py              # 侧边栏 + 顶栏 + 内容
│       │   ├── auth_layout.py              # 居中登录布局
│       │   └── blank_layout.py             # 空白布局
│       │
│       ├── templates/                      # ═══ L4 业务模板 ═══
│       │   ├── __init__.py
│       │   ├── login_page.py
│       │   ├── dashboard_page.py
│       │   └── settings_page.py
│       │
│       └── assets/                         # 内置资源
│           ├── icons/                      # SVG 图标
│           │   ├── check.svg
│           │   └── ...
│           └── fonts/
│               └── Roboto-Regular.ttf
│
├── tests/                                  # ═══ 测试 ═══
│   ├── conftest.py                         # pytest 全局 fixture
│   ├── unit/                               # 单元测试（对照 src 结构）
│   │   ├── core/
│   │   ├── components/
│   │   └── ...
│   ├── integration/                        # 集成测试
│   └── visual/                             # 视觉回归测试（截图对比）
│       └── snapshots/
│
├── examples/                               # ═══ 示例 ═══
│   ├── 01_hello_quasar.py
│   ├── 02_button_gallery.py
│   ├── 03_form_validation.py
│   ├── 04_dashboard.py
│   └── gallery/
│       └── components_gallery.py           # 组件画廊总入口
│
├── docs/                                   # ═══ 文档站（MkDocs）═══
│   ├── index.md
│   ├── quickstart.md
│   ├── architecture.md
│   ├── theming.md
│   ├── components/
│   │   ├── button.md
│   │   └── ...
│   └── api/                                # mkdocstrings 自动生成
│
├── benchmarks/                             # ═══ 性能基准 ═══
│   ├── bench_paint.py
│   └── bench_theme_switch.py
│
├── scripts/                                # ═══ 工程化脚本 ═══
│   ├── build.py                            # Nuitka 打包
│   ├── release.py                          # 发版流程
│   └── gen_icons.py                        # SVG 图标生成
│
├── .github/                                # ═══ CI/CD ═══
│   └── workflows/
│       ├── ci.yml                          # pytest + mypy + ruff
│       ├── release.yml                     # PyPI 发布
│       └── docs.yml                        # 文档自动部署
│
├── .pre-commit-config.yaml                 # 提交前自动化检查
├── .editorconfig                           # 编辑器统一规范
├── .gitignore
├── pyproject.toml                          # ★ PEP 621 打包配置
├── mkdocs.yml                              # 文档站配置
├── README.md
├── README_EN.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
└── LICENSE