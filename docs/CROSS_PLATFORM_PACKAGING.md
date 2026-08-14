# Windows and macOS Packaging Plan

## Shared Components

The following components are shared across both platforms:

- PDF parsers, categorization rules, and analysis logic.
- Ollama API address and JSON Schema.
- The `llama3.2:3b` model tag.
- Prompt version, confidence threshold, and cache format.
- Streamlit interface code.

Application code must not hard-code a Windows user directory, an NVIDIA path, or a macOS application directory. The local model is accessed through `http://localhost:11434`, so Ollama handles the differences between an NVIDIA GPU on Windows and Apple Silicon/Metal on macOS.

## Platform Installation Entry Points

- Windows: `scripts/setup_local_llm_windows.ps1`
- macOS: `scripts/setup_local_llm_macos.sh`
- Windows application launch: the batch launcher in the project root.
- macOS application launch: `scripts/run_app_macos.command`

The macOS files may need executable permission before their first use:

```bash
chmod +x scripts/setup_local_llm_macos.sh scripts/run_app_macos.command
```

## Final Distributions

The project should produce two platform-specific distributions rather than one cross-platform binary:

- A Windows x64 package.
- A macOS Apple Silicon package. Intel Mac support should be validated separately or provided through a universal2 build.

PyInstaller output depends on the build operating system and Python version. A Windows package must therefore be built on Windows, and a macOS package must be built on macOS. Both builds can use the same repository and automated test suite.

Reference: https://pyinstaller.org/en/stable/operating-mode.html

Ollama and the approximately 2 GB model should be installed as first-run components instead of being embedded in the main application package. This allows the model to be updated independently, reduces application update size, and lets users disable or remove Local AI without affecting rule-based categorization.

## Pre-Release Checklist

Both platforms must verify the following:

1. Rule-based categorization and PDF analysis work without Ollama installed.
2. If Ollama is installed but the model is missing, the interface reports that Local AI is unavailable without crashing.
3. When the model is available, only merchant descriptions are sent to the local API.
4. The same set of confirmed merchants produces the same structured output on both platforms.
5. The complete automated suite and real-PDF regression tests run independently on Windows and macOS.
