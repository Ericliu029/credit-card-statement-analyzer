Credit Card Statement Analyzer - macOS 安装说明

1. 请先把整个文件夹解压到 Mac 本地，例如“应用程序”或“文稿”。
2. 双击“Install Credit Card Analyzer.command”。
3. 如果 macOS 阻止第一次打开，请按住 Control 点击该文件，选择“打开”，再确认一次。
4. 安装器会在本文件夹内准备独立的 Python 环境和全部程序依赖，不会修改系统 Python。
5. 若电脑还没有 Ollama，安装器会打开 Ollama 官方下载页。完成 Ollama 安装后，再运行一次安装器，即可下载本地分类模型。
6. 以后只需双击“Start Credit Card Analyzer.command”。浏览器会自动打开程序。

注意事项

- Ollama 和 llama3.2:3b 用于本地 AI 商户分类。账单内容不会因为分类而上传到云端。
- 第一次下载模型需要网络，约占 2 GB 磁盘空间。之后可离线使用。
- 程序、Python 环境和模型彼此独立。删除本程序文件夹不会自动删除 Ollama 模型。
- 本安装包同时适用于 Apple Silicon 和 Intel Mac；所需组件会按当前 Mac 自动选择。
