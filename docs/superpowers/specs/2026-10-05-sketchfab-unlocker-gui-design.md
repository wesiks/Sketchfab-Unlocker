# Sketchfab Unlocker — Design Specification

## Overview
Sketchfab Unlocker is a desktop utility for Windows designed to download and unlock public 3D models from Sketchfab without requiring an account or API keys. This project evolves the command-line utility into a modern, high-end desktop application featuring a dark-mode graphical user interface (GUI), clean asset output (removing temporary decryption artifacts), a portable executable build, updated documentation, and publication to GitHub under the user `wesiks`.

## Strict Non-Negotiable Constraint
- **No explanations or comments in any code files**: All Python and script files written or modified must contain zero code comments (`#`) and zero explanatory docstrings.

## Core Features & Architecture

### 1. Core Engine Optimization (`main.py`)
- **Clean Output Routine**:
  - Automatically remove decryption artifacts upon successful conversion to `.gltf` / `.glb`.
  - Artifacts removed: `key.txt`, `key2.txt`, `file.osgjs`, `model_file.bin`, `model_file_wireframe.bin`, `textures_manifest.json`, and any temporary `.gz` or `.binz` files.
  - Final deliverables retained:
    - Main model file (`<model_name>.gltf` or `<model_name>.glb`)
    - Necessary glTF binary buffers (`*.bin` matching glTF uri references)
    - `textures/` directory containing extracted textures
    - `info.json` containing metadata (author, title, source URL)
  - Controlled by a `clean_output=True` argument/flag (enabled by default).
- **Callback API**:
  - Provide fine-grained status callbacks for UI: step name, human-readable status, and percent progress.

### 2. High-End Desktop UI (`gui.py`)
- **Technology**: Native Python `tkinter` + `ttk` styled to agency-grade dark aesthetics.
- **Visual Design System**:
  - Background: Deep Obsidian (`#0B0E14`)
  - Card/Container: Midnight Slate (`#151922`), inner border `#252D3D`
  - Accent / CTA: Indigo Cyan (`#4F46E5` / `#6366F1`), hover `#4338CA`
  - Text: Primary `#F3F4F6`, Muted `#9CA3AF`, Success `#10B981`, Warning `#F59E0B`, Danger `#EF4444`
  - Typography: `Segoe UI Variable Display`, `Segoe UI`, `Consolas` for logs.
- **Layout & Structure**:
  - Header: Application title, eyebrow badge "v2.0 Portable", status pill badges for `Node.js` and `Tools`.
  - Input Section: Multi-line text field with placeholder for URLs, "Вставить из буфера" button, "Очистить" button.
  - Settings Bar:
    - Output directory picker (defaults to `./downloads`) with browse button.
    - Checkbox: "Очищать временные файлы (.key, .osgjs)" (checked by default).
    - Proxy input field (optional).
  - Action & Progress:
    - Prominent action button: "Скачать модель".
    - Animated / determinate progress bar with current status label.
    - Button to open destination directory in Windows Explorer.
  - Live Console Log:
    - Styled scrollable terminal output for download progress details, collapsible or always visible at bottom.
  - Concurrency:
    - Downloads execute on a background daemon worker thread to prevent UI freezing.

### 3. Portable Launchers & Build
- `start.bat`: Runs `gui.py` using `pythonw` (silent launcher without console window).
- `SketchfabUnlocker.exe`: Portable standalone executable built via PyInstaller with `--noconsole` and relative paths to `./tools`.

### 4. Privacy & Data Protection
- Scrub any personal local machine paths (`C:\Users\Fasok\...`), Windows usernames, or credentials.
- Ensure `downloads/` directory only contains `.gitkeep`.
- Update `.gitignore` to prevent any personal files, downloaded assets, temporary keys, logs, or pyinstaller build artifacts from entering git.

### 5. Documentation
- Update `README.md` (English) and `README.ru.md` (Russian):
  - Branded as **Sketchfab Unlocker** by **wesiks**.
  - Document GUI usage, portable EXE, clean output feature, and CLI options.
  - Remove irrelevant or stale text.

### 6. GitHub Publication
- Initialize git repository.
- Verify safe directory configuration.
- Commit all clean files.
- Publish public repository `wesiks/Sketchfab-Unlocker` via GitHub CLI (`gh repo create wesiks/Sketchfab-Unlocker --public --source=. --push`).

## Verification Plan
1. Launch and test `gui.py` directly.
2. Run test download with clean output enabled to verify model and textures exist and `key.txt` is removed.
3. Verify zero comments exist in code.
4. Verify no personal data exists in repository files.
5. Create and push repository to GitHub.
