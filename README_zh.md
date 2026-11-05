# PySide-Quasar

> **A Quasar-inspired, enterprise-grade component framework for PySide.**  
> Material Design components. Pure `QPainter` rendering. Zero QSS dependency.
> 
[English](https://github.com/eagleye-china/pyside-quasar/blob/master/README.md)

[![PyPI version](https://img.shields.io/pypi/v/pyside-quasar?color=blue&label=PyPI)](https://pypi.org/project/pyside-quasar/)
[![Python Version](https://img.shields.io/pypi/pyversions/pyside-quasar)](https://pypi.org/project/pyside-quasar/)
[![License](https://img.shields.io/badge/license-MIT-green)](https://github.com/eagleye-china/pyside-quasar/blob/master/LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/eagleye-china/pyside-quasar?style=social)](https://github.com/eagleye-china/pyside-quasar)
**PySide-Quasar** 是面向企业桌面应用的 PySide UI 组件库，对标 Quasar Framework 的 Material Design 设计规范。  
基于原生 `QPainter` 自绘渲染，**完全不依赖 QSS（Qt Style Sheets）**，规避了 Qt 样式表复杂兼容、性能抖动、跨平台渲染不一致等痛点。非常适合工业组态、后台管理、监控大屏及企业级业务桌面客户端。

---

## ✨ 核心特性

- 🚀 **Zero QSS 渲染**：所有组件均由 `QPainter` 原生手绘，无样式表，渲染稳定可控，告别样式崩坏。
- 🧩 **企业级组件库**：提供 Button, Dialog, Badge, Avatar, Checkbox 等工业级高频组件。
- 🔮 **前瞻版本解耦**：基于 PySide 抽象层，当前完美兼容 `PySide6`，并**前瞻支持未来的 PySide7/8**，平滑迁移。
- 🎨 **智能主题系统**：内置亮/暗双主题自适应，高对比度文字自动计算，全局主色、圆角、密度一键切换。
- 🖥️ **高 DPI 完美适配**：全系控件按逻辑像素与设备 DPR 深度优化，Retina / 4K 屏零糊边、零锯齿。
- 🛡️ **全量类型注解**：重度 Typed，完美适配 VSCode / PyCharm 静态提示，企业级代码审查无压力。
- 📦 **轻量化交付**：无 WebView、无前端资源，纯 Python 生态，PyInstaller 打包体积极小。

> **适用场景**：工业监控客户端、MES 系统、后台管理桌面端、设备调试工具、数据看板等。

---

## 📦 安装

> 当前版本为 Alpha 预发布版，仅在 TestPyPI 提供测试。

```bash
# 从 TestPyPI 安装指定 Beta 版本
pip install -i https://test.pypi.org/simple/ pyside-quasar==0.2.0