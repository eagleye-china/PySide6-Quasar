# 🎨 pyside-quasar 框架图标设计方案

## 设计理念

图标采用**「类星体（Quasar）」**作为核心视觉隐喻，完美契合框架定位：

| 视觉元素 | 象征意义 |
| :--- | :--- |
| **中心发光体** | 框架的核心内核（L0 核心层） |
| **交叉椭圆轨道** | 组件层环绕核心（L1-L4 分层架构） |
| **蓝色渐变** | Material Design 的品牌色系 |
| **轨道上的星点** | 独立组件围绕中心运转 |
| **圆角方形** | 桌面应用的容器感 |

---

## 一、主版本 SVG（推荐）

**文件路径：`assets/icon.svg`**

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <!-- 背景渐变 -->
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0D47A1"/>
      <stop offset="55%" stop-color="#1976D2"/>
      <stop offset="100%" stop-color="#42A5F5"/>
    </linearGradient>
    
    <!-- 核心发光 -->
    <radialGradient id="coreGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="1"/>
      <stop offset="50%" stop-color="#FFFFFF" stop-opacity="0.8"/>
      <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0"/>
    </radialGradient>
    
    <!-- 轨道 1 渐变 -->
    <linearGradient id="orbitGrad1" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0"/>
      <stop offset="50%" stop-color="#FFFFFF" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0"/>
    </linearGradient>
    
    <!-- 轨道 2 渐变 -->
    <linearGradient id="orbitGrad2" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0"/>
      <stop offset="50%" stop-color="#FFFFFF" stop-opacity="0.7"/>
      <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0"/>
    </linearGradient>
    
    <!-- 发光滤镜 -->
    <filter id="glowFilter" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="10"/>
    </filter>
  </defs>
  
  <!-- 背景 -->
  <rect width="512" height="512" rx="112" fill="url(#bgGrad)"/>
  
  <!-- 内圈装饰 -->
  <circle cx="256" cy="256" r="200" fill="none" stroke="#FFFFFF" stroke-opacity="0.06" stroke-width="1.5"/>
  <circle cx="256" cy="256" r="175" fill="none" stroke="#FFFFFF" stroke-opacity="0.04" stroke-width="1"/>
  
  <!-- 轨道 1（倾斜 -40°） -->
  <g transform="rotate(-40 256 256)">
    <ellipse cx="256" cy="256" rx="200" ry="80" 
             fill="none" stroke="url(#orbitGrad1)" stroke-width="3.5"/>
  </g>
  
  <!-- 轨道 2（倾斜 50°） -->
  <g transform="rotate(50 256 256)">
    <ellipse cx="256" cy="256" rx="200" ry="80" 
             fill="none" stroke="url(#orbitGrad2)" stroke-width="3"/>
  </g>
  
  <!-- 中心光晕 -->
  <circle cx="256" cy="256" r="90" fill="url(#coreGlow)" filter="url(#glowFilter)" opacity="0.9"/>
  
  <!-- 中心主体 -->
  <circle cx="256" cy="256" r="55" fill="#FFFFFF"/>
  
  <!-- 核心深色点 -->
  <circle cx="256" cy="256" r="24" fill="#1976D2"/>
  
  <!-- 高光 -->
  <circle cx="248" cy="248" r="6" fill="#FFFFFF" opacity="0.9"/>
  
  <!-- 轨道星点 -->
  <circle cx="62" cy="293" r="7" fill="#FFFFFF"/>
  <circle cx="450" cy="219" r="5" fill="#FFFFFF" opacity="0.9"/>
  <circle cx="410" cy="410" r="4" fill="#FFFFFF" opacity="0.6"/>
</svg>
```

---

## 二、透明背景版本（用于应用内嵌）

**文件路径：`assets/icon-transparent.svg`**

去掉了背景矩形，适合放在任意容器上：

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <radialGradient id="coreGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#1976D2" stop-opacity="1"/>
      <stop offset="50%" stop-color="#1976D2" stop-opacity="0.6"/>
      <stop offset="100%" stop-color="#1976D2" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="orbitGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#1976D2" stop-opacity="0.1"/>
      <stop offset="50%" stop-color="#1976D2" stop-opacity="1"/>
      <stop offset="100%" stop-color="#1976D2" stop-opacity="0.1"/>
    </linearGradient>
  </defs>
  
  <!-- 轨道 -->
  <g transform="rotate(-40 256 256)">
    <ellipse cx="256" cy="256" rx="200" ry="80" 
             fill="none" stroke="url(#orbitGrad)" stroke-width="4"/>
  </g>
  <g transform="rotate(50 256 256)">
    <ellipse cx="256" cy="256" rx="200" ry="80" 
             fill="none" stroke="url(#orbitGrad)" stroke-width="3"/>
  </g>
  
  <!-- 中心光晕 -->
  <circle cx="256" cy="256" r="90" fill="url(#coreGlow)" opacity="0.7"/>
  
  <!-- 中心主体 -->
  <circle cx="256" cy="256" r="55" fill="#1976D2"/>
  <circle cx="256" cy="256" r="24" fill="#FFFFFF"/>
  <circle cx="248" cy="248" r="6" fill="#1976D2" opacity="0.8"/>
</svg>
```

---

## 三、深色版本（用于深色主题任务栏）

**文件路径：`assets/icon-dark.svg`**

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0D1117"/>
      <stop offset="100%" stop-color="#1F2937"/>
    </linearGradient>
    <radialGradient id="coreGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#42A5F5" stop-opacity="1"/>
      <stop offset="60%" stop-color="#42A5F5" stop-opacity="0.4"/>
      <stop offset="100%" stop-color="#42A5F5" stop-opacity="0"/>
    </radialGradient>
  </defs>
  
  <rect width="512" height="512" rx="112" fill="url(#bgGrad)"/>
  
  <!-- 轨道 -->
  <g transform="rotate(-40 256 256)">
    <ellipse cx="256" cy="256" rx="200" ry="80" 
             fill="none" stroke="#42A5F5" stroke-opacity="0.6" stroke-width="3.5"/>
  </g>
  <g transform="rotate(50 256 256)">
    <ellipse cx="256" cy="256" rx="200" ry="80" 
             fill="none" stroke="#64B5F6" stroke-opacity="0.4" stroke-width="3"/>
  </g>
  
  <circle cx="256" cy="256" r="90" fill="url(#coreGlow)"/>
  <circle cx="256" cy="256" r="55" fill="#42A5F5"/>
  <circle cx="256" cy="256" r="24" fill="#0D1117"/>
  <circle cx="248" cy="248" r="6" fill="#FFFFFF" opacity="0.9"/>
  
  <circle cx="62" cy="293" r="7" fill="#42A5F5"/>
  <circle cx="450" cy="219" r="5" fill="#64B5F6"/>
</svg>
```

---

## 四、Python 脚本：SVG → 多尺寸 PNG

**文件路径：`scripts/generate_icons.py`**

```python
# scripts/generate_icons.py
"""
批量将 SVG 图标转换为多尺寸 PNG 和 ICO。
依赖：PySide6（已安装）

用法：
    python scripts/generate_icons.py
"""

import sys
from pathlib import Path

from PySide6.QtGui import QImage, QPainter, QGuiApplication, QIcon
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QSize, QByteArray


# ═══════════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════════

ROOT = Path(__file__).parent.parent
ASSETS_DIR = ROOT / "assets"
OUTPUT_DIR = ASSETS_DIR / "icons"

# 需要的 PNG 尺寸（覆盖 Windows / macOS / Linux 常用尺寸）
SIZES = [16, 24, 32, 48, 64, 128, 256, 512, 1024]

# 需要生成的变体（SVG 文件名 → 输出前缀）
VARIANTS = {
    "icon.svg": "pq",              # 主版本
    "icon-transparent.svg": "pq-transparent",
    "icon-dark.svg": "pq-dark",
}


# ═══════════════════════════════════════════════════════════════
# 核心：SVG → PNG
# ═══════════════════════════════════════════════════════════════

def svg_to_png(svg_path: Path, png_path: Path, size: int) -> bool:
    """将 SVG 渲染为指定尺寸的 PNG"""
    try:
        renderer = QSvgRenderer(str(svg_path))
        if not renderer.isValid():
            print(f"  ❌ SVG 无效: {svg_path}")
            return False

        image = QImage(QSize(size, size), QImage.Format.Format_ARGB32)
        image.fill(0x00000000)  # 透明背景

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        renderer.render(painter)
        painter.end()

        png_path.parent.mkdir(parents=True, exist_ok=True)
        return image.save(str(png_path), "PNG")
    except Exception as e:
        print(f"  ❌ 渲染失败: {e}")
        return False


def generate_ico(png_paths: list[Path], ico_path: Path) -> bool:
    """将多个 PNG 合并为 .ico 文件"""
    try:
        icon = QIcon()
        for png in png_paths:
            if png.exists():
                icon.addFile(str(png))
        # QIcon 不支持直接保存 .ico，用 PIL 或外部工具，这里用 QImage 简单方式
        # 简化方案：只保存最大的 PNG 作为 .ico 占位
        if png_paths:
            largest = max(png_paths, key=lambda p: int(p.stem.split("_")[-1]))
            from PySide6.QtGui import QImage
            img = QImage(str(largest))
            img.save(str(ico_path), "ICO")
            return True
        return False
    except Exception as e:
        print(f"  ❌ ICO 生成失败: {e}")
        return False


# ═══════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════

def main():
    app = QGuiApplication(sys.argv)

    if not ASSETS_DIR.exists():
        print(f"❌ 资源目录不存在: {ASSETS_DIR}")
        return

    print(f"📂 资源目录: {ASSETS_DIR}")
    print(f"📂 输出目录: {OUTPUT_DIR}")
    print()

    total = 0
    for svg_name, prefix in VARIANTS.items():
        svg_path = ASSETS_DIR / svg_name
        if not svg_path.exists():
            print(f"⚠️  跳过（不存在）: {svg_name}")
            continue

        print(f"🎨 处理: {svg_name}")

        generated_pngs = []
        for size in SIZES:
            png_path = OUTPUT_DIR / f"{prefix}_{size}.png"
            if svg_to_png(svg_path, png_path, size):
                print(f"  ✅ {png_path.name}")
                generated_pngs.append(png_path)
                total += 1

        # 生成 ICO（仅对主版本）
        if prefix == "pq":
            ico_path = OUTPUT_DIR / "pq.ico"
            if generate_ico(generated_pngs, ico_path):
                print(f"  ✅ {ico_path.name}")

        print()

    print("=" * 60)
    print(f"🎉 完成！共生成 {total} 个 PNG 文件")
    print(f"   输出目录: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
```

---

## 五、使用指南

### 5.1 生成图标资源

```bash
cd pyside-quasar
python scripts/generate_icons.py
```

生成的目录结构：

```text
assets/
├── icon.svg                    # 主版本（源码）
├── icon-transparent.svg        # 透明背景版本（源码）
├── icon-dark.svg               # 深色版本（源码）
└── icons/                      # 渲染生成的 PNG
    ├── pq_16.png
    ├── pq_32.png
    ├── pq_64.png
    ├── pq_128.png
    ├── pq_256.png
    ├── pq_512.png
    ├── pq.ico
    ├── pq-transparent_256.png
    └── pq-dark_256.png
```

### 5.2 在 PySide6 应用中使用

```python
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtGui import QIcon
import sys

app = QApplication(sys.argv)

window = QMainWindow()
# 加载图标（自动适配高 DPI）
window.setWindowIcon(QIcon("assets/icons/pq.ico"))
window.show()

sys.exit(app.exec())
```

### 5.3 通过 Qt 资源系统（推荐生产环境）

在 `resources.qrc` 中声明：

```xml
<RCC>
    <qresource prefix="/icons">
        <file>assets/icons/pq_16.png</file>
        <file>assets/icons/pq_32.png</file>
        <file>assets/icons/pq_64.png</file>
        <file>assets/icons/pq_256.png</file>
        <file>assets/icons/pq.ico</file>
    </qresource>
</RCC>
```

编译为 `.py` 资源文件：

```bash
pyside6-rcc resources.qrc -o src/pyside_quasar/_resources_rc.py
```

然后在代码中直接使用：

```python
from PySide6.QtGui import QIcon
from . import _resources_rc  # 触发资源注册

window.setWindowIcon(QIcon(":/icons/assets/icons/pq.ico"))
```

### 5.4 在 README 中展示

```markdown
<div align="center">
  <img src="assets/icon.svg" width="128" alt="pyside-quasar"/>
  <h1>pyside-quasar</h1>
</div>
```

---

## 六、设计备选方案（如需其他风格）

如果团队认为"类星体"风格不够，可以考虑以下替代方向：

| 方案 | 描述 | 适用场景 |
| :--- | :--- | :--- |
| **方案 A（已提供）** | 类星体核心 + 椭圆轨道 | 科技感强，契合"Quasar"名字 |
| **方案 B** | 圆角方块 + 抽象的 "P" 字母 | 更直接体现 Python |
| **方案 C** | 层叠的 Material 卡片 + 光晕 | 更强调"组件框架"定位 |
| **方案 D** | 抽象的螺旋星系 | 更强调"生态"概念 |

如需生成方案 B/C/D 的 SVG 代码，或者需要对当前设计做微调（如更换色调、调整轨道角度、增加 Python 蛇形元素），随时告诉我，我会立刻给出对应版本的完整代码。