# PySide-Quasar ⚛️

> **Enterprise-grade UI components for PySide. Quasar aesthetics, Pure QPainter, Zero QSS.**

**English** | [简体中文](https://github.com/eagleye-china/pyside-quasar/blob/master/README_zh.md)

[![PyPI version](https://img.shields.io/pypi/v/pyside-quasar?color=blue&label=PyPI)](https://pypi.org/project/pyside-quasar/)
[![Python Version](https://img.shields.io/pypi/pyversions/pyside-quasar)](https://pypi.org/project/pyside-quasar/)
[![License](https://img.shields.io/badge/license-MIT-green)](https://github.com/eagleye-china/pyside-quasar/blob/master/LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/eagleye-china/pyside-quasar?style=social)](https://github.com/eagleye-china/pyside-quasar)
**PySide-Quasar** is a modern, enterprise-grade UI component framework for PySide. Inspired by the design language of Vue's *Quasar Framework*, it brings Material Design aesthetics to desktop applications using **pure `QPainter` rendering** with **ZERO QSS (Qt Style Sheets) dependencies**. 

It eliminates the common pain points of QSS—such as cross-platform rendering inconsistencies, performance bottlenecks, and style breakages—making it the perfect choice for industrial control panels, monitoring dashboards, and complex enterprise desktop clients.

---

## 📸 Gallery

> 💡 *Here is a preview of the core components. (Replace the image URLs below with your actual GIFs!)*

| Components | Showcase |
| :---: | :---: |
| **Buttons & Checkboxes** | <img src="https://via.placeholder.com/600x300/1E1E1E/D4D4D4?text=Buttons+and+Checkboxes+GIF" alt="Buttons and Checkboxes" width="400"/> |
| **Dialogs & Badges** | <img src="https://via.placeholder.com/600x300/1E1E1E/D4D4D4?text=Dialog+and+Badge+GIF" alt="Dialog and Badge" width="400"/> |

---

## 🤔 Why PySide-Quasar? (The "Zero QSS" Philosophy)

Traditional PySide/PyQt applications rely heavily on QSS. While fine for small apps, QSS scales poorly in enterprise systems. Here is why we went completely QSS-free:

| Feature | Traditional QSS Approach | **PySide-Quasar (Our Approach)** |
| :--- | :--- | :--- |
| **Rendering** | OS-dependent, often buggy with complex gradients. | **Pixel-perfect** across Windows, macOS, and Linux. |
| **Performance** | High CPU usage during rapid updates (e.g., industrial data). | **Blazing fast** with optimized native `QPainter`. |
| **High-DPI (4K)** | Blurry borders, broken scaling, jagged edges. | **Crisp & Sharp** automatically adapts to devicePixelRatio. |
| **Maintenance** | Hundreds of lines of unstructured CSS-like strings. | **Clean Python** with strongly-typed APIs and theme engines. |
| **PySide7/8 Future**| Style breakages requiring extensive rewrites. | **Future-proof**, seamlessly migrates to future PySide versions. |

---

## ✨ Core Features

- 🚀 **Zero QSS Dependency** – Everything is drawn natively via `QPainter`.
- 🧩 **Quasar-Inspired Design** – Beautiful Material Design components with smooth micro-animations.
- 🔮 **Future-Proof API** – Built on an abstraction layer. Currently binds to `PySide6`, but fully prepared for `PySide7/8`.
- 🖥️ **4K / Retina Ready** – Deeply optimized for High-DPI screens. No more blurry icons or jagged lines.
- 🎨 **Dynamic Theme Engine** – Native Light/Dark mode support. Automatic high-contrast text calculation.
- 🛡️ **Enterprise-Grade Typed** – 100% Type hints. Perfect for PyCharm/VSCode intellisense and strict CI pipelines.
- 📦 **Lightweight & Packable** – No WebViews, no heavy assets. Very friendly for `PyInstaller`.

---

## 📦 Installation

```bash
pip install pyside-quasar
```

**Dependencies:**
- `PySide6 >= 6.6.0`
- `typing-extensions`

---

## 🚀 Quick Start

```python
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from pyside_quasar.components import Button, Checkbox, Dialog
from pyside_quasar.theme import QuasarTheme

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 1. Apply Dark Theme (Native rendering)
    QuasarTheme.apply_dark()

    # 2. Create your main window
    win = QMainWindow()
    win.resize(800, 600)
    win.setWindowTitle("PySide-Quasar Demo")

    # 3. Use pure QPainter components
    central = QWidget()
    layout = QVBoxLayout(central)
    
    btn = Button(text="Open Dialog", color="primary", size="lg")
    chk = Checkbox(text="Enable Advanced Settings", checked=True)
    
    layout.addWidget(btn)
    layout.addWidget(chk)
    win.setCentralWidget(central)
    
    win.show()
    sys.exit(app.exec())
```

---

## 🧩 Components Ecosystem

We are actively expanding the ecosystem. Here is the current status:

| Module | Stable Components | In Development |
| :--- | :--- | :--- |
| **Primitives** | `Button`, `Checkbox`, `Avatar`, `Badge` | `Input`, `Switch`, `Select` |
| **Containers** | `Dialog` | `Card`, `Tabs`, `Drawer` |
| **Feedback** | - | `Toast`, `Notify`, `Progress` |
| **Data** | - | `Table`, `Pagination` |

---

## 🎨 Theming System

Say goodbye to messy stylesheets. Control your entire app's look with Python.

```python
from pyside_quasar.theme import QuasarTheme

# 1. Toggle Light/Dark mode
QuasarTheme.apply_light()
QuasarTheme.apply_dark()

# 2. Set your enterprise brand color
QuasarTheme.set_brand_color("#1976D2")

# 3. Global border radius configuration
QuasarTheme.set_border_radius(6)
```

---

## 📐 Roadmap & Version Strategy

Because our package name **`pyside-quasar`** does not contain a version number, you are protected from ecosystem churn.

- **`v1.x`** – Active development, binding to **PySide6**.
- **`v2.x`** – Seamless transition to **PySide7** (Zero code changes for UI layers).
- **`v3.x`** – Future-ready for **PySide8**.

---

## 🤝 Contributing

We welcome contributions from the global community! Whether it's a bug report, a new component, or a documentation fix, your help is appreciated.

```bash
# Clone the repository
git clone https://github.com/eagleye-china/pyside-quasar.git
cd pyside-quasar

# Install in editable mode for development
pip install -e .

# Build the package
python -m build
```

If you find this project useful, please consider giving it a ⭐️ on GitHub! It means a lot to us.

---

## 📜 License

MIT License. Commercial use is allowed. See the [LICENSE](LICENSE) file for details.