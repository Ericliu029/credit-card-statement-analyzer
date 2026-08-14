from __future__ import annotations

import stat
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
OUTPUT = DIST / "Credit-Card-Statement-Analyzer-macOS.zip"
PACKAGE_ROOT = "Credit Card Statement Analyzer"

SOURCE_DIRS = (
    "assets",
    "categorization",
    "data",
    "docs",
    "models",
    "parsers",
    "services",
)
SOURCE_FILES = ("app.py", "README.md", "requirements.txt")
MACOS_FILES = (
    "Install Credit Card Analyzer.command",
    "Start Credit Card Analyzer.command",
    "README-macOS.txt",
)

EXCLUDED_NAMES = {"__pycache__", ".pytest_cache", ".DS_Store"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".log", ".pdf"}


def archive_name(relative: Path) -> str:
    return f"{PACKAGE_ROOT}/{relative.as_posix()}"


def add_bytes(bundle: zipfile.ZipFile, name: str, content: bytes, executable: bool = False) -> None:
    info = zipfile.ZipInfo(name)
    info.create_system = 3
    mode = stat.S_IFREG | (0o755 if executable else 0o644)
    info.external_attr = mode << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    bundle.writestr(info, content)


def add_file(bundle: zipfile.ZipFile, source: Path, relative: Path) -> None:
    executable = source.suffix in {".command", ".sh"}
    add_bytes(bundle, archive_name(relative), source.read_bytes(), executable)


def should_include(path: Path) -> bool:
    return not any(part in EXCLUDED_NAMES for part in path.parts) and path.suffix.lower() not in EXCLUDED_SUFFIXES


def build() -> Path:
    DIST.mkdir(exist_ok=True)

    with zipfile.ZipFile(OUTPUT, "w") as bundle:
        for filename in SOURCE_FILES:
            source = ROOT / filename
            add_file(bundle, source, Path(filename))

        for dirname in SOURCE_DIRS:
            source_dir = ROOT / dirname
            for source in sorted(path for path in source_dir.rglob("*") if path.is_file()):
                relative = source.relative_to(ROOT)
                if not should_include(relative):
                    continue
                if relative.as_posix() in {
                    "data/custom_merchant_rules.json",
                    "data/llm_category_cache.json",
                }:
                    add_bytes(bundle, archive_name(relative), b"{}\n")
                else:
                    add_file(bundle, source, relative)

        for filename in MACOS_FILES:
            source = ROOT / "macos" / filename
            add_file(bundle, source, Path(filename))

    return OUTPUT


if __name__ == "__main__":
    print(build())
