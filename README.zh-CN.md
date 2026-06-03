# ScriptClipper

ScriptClipper 是一个面向短视频创作者的视频脚本时间轴辅助工具，用于管理 A-Roll 口播、B-Roll 画面、结构化脚本和时间轴节奏。

## 功能特性

- A-Roll / B-Roll 双轨时间轴
- 结构化脚本编辑
- 内容细化调节
- 片段拖动和时长调整
- 中英文界面切换
- `.sclip` 工程保存和打开
- TXT 导入
- Markdown / TXT / JSON 导出
- Windows 绿色版运行

## 下载和运行

1. 前往 GitHub Releases。
2. 下载 `ScriptClipper-v0.1.0-windows-x64.zip`。
3. 解压压缩包。
4. 双击 `ScriptClipper.exe` 运行。

## 本地开发

安装依赖：

```powershell
pip install -r requirements.txt
```

运行项目：

```powershell
python main.py
```

打包项目：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

## 打包说明

项目使用 PyInstaller 打包 Windows 绿色版应用。当前仓库已包含稳定打包脚本：

```text
scripts/build_windows.ps1
```

打包产物生成在 `release/` 目录。`release/`、`build/`、`dist/` 不提交到源码仓库，只作为 GitHub Release 附件发布。

## 项目结构

```text
.
├── assets/                  # 应用图标等静态资源
├── scriptclipper/            # 应用源码
│   ├── core/                 # 数据模型、文件读写、导出、i18n
│   ├── resources/            # Qt 样式和主题
│   └── ui/                   # PySide6 界面组件
├── scripts/                  # 构建脚本
├── main.py                   # 程序入口
├── ScriptClipper.spec        # PyInstaller 配置
├── README.md                 # 英文说明
└── README.zh-CN.md           # 简体中文说明
```

## 版本说明

当前版本：`v0.1.0`

`Initial Preview`：首个预览版本，提供视频脚本结构化编辑和时间轴编排基础能力。

## 已知问题

- 当前是预览版本，主要面向脚本和时间轴编排。
- 暂不是真正的视频剪辑渲染软件。
- 暂未提供安装器，Windows 版本以绿色版压缩包发布。

## 后续计划

- 优化时间轴交互和缩放体验
- 增强素材管理能力
- 增加更多导出格式
- 后续考虑视频预览和 FFmpeg 能力

## 许可证

MIT License

## 贡献说明

后续功能通过分支和 PR 管理。请不要直接在 `main` 分支修改代码。
