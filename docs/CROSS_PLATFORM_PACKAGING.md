# Windows 与 macOS 封装方案

## 共享部分

以下内容在两个平台完全共用：

- PDF 解析器、分类规则和分析逻辑。
- Ollama API 地址与 JSON Schema。
- 模型标签 `llama3.2:3b`。
- 提示词版本、置信度阈值和缓存格式。
- Streamlit 页面代码。

应用代码不得写死 Windows 用户目录、NVIDIA 路径或 macOS 应用目录。本地模型通过 `http://localhost:11434` 访问，因此 Windows 的 NVIDIA GPU 与 macOS 的 Apple Silicon/Metal 差异由 Ollama 处理。

## 平台安装入口

- Windows：`scripts/setup_local_llm_windows.ps1`
- macOS：`scripts/setup_local_llm_macos.sh`
- Windows 应用启动：项目根目录的批处理启动器。
- macOS 应用启动：`scripts/run_app_macos.command`

macOS 文件首次使用时可能需要执行：

```bash
chmod +x scripts/setup_local_llm_macos.sh scripts/run_app_macos.command
```

## 最终发行包

最终应生成两个发行物，而不是一个跨系统二进制文件：

- Windows x64 安装包。
- macOS Apple Silicon 安装包；如需支持 Intel Mac，应单独验证或生成 universal2 构建。

PyInstaller 的输出与构建时操作系统和 Python 版本相关，因此 Windows 包必须在 Windows 构建，macOS 包必须在 macOS 构建。两个构建可以使用同一代码仓库和自动化测试。

参考：https://pyinstaller.org/en/stable/operating-mode.html

Ollama 与约 2GB 模型建议作为首次运行组件安装，而不是直接塞入主应用包。这样可以独立更新模型、减少应用更新体积，并允许用户关闭或卸载 Local AI 而不影响规则分类功能。

## 发布前检查

两个平台都必须验证：

1. 不安装 Ollama 时，规则分类和 PDF 分析仍可运行。
2. 安装 Ollama 但未下载模型时，页面显示不可用状态且不崩溃。
3. 模型可用时，只向本地 API 发送商户描述。
4. 同一组已确认商户在两个平台得到相同结构的输出。
5. Windows 和 macOS 分别执行完整测试与真实 PDF 回归测试。
