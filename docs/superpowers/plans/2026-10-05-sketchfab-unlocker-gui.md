# Sketchfab Unlocker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a modern desktop GUI for Sketchfab Unlocker with clean output (auto-deleting temporary decryption files), portable launchers, customized documentation for `wesiks`, and publish it cleanly to GitHub.

**Architecture:** A lightweight high-end dark GUI (`gui.py`) built on `tkinter`/`ttk` wrapping the core engine in `main.py` via background threads and callbacks. The core engine is updated with a `clean_output` pipeline that deletes intermediate decryption artifacts (`key.txt`, `file.osgjs`, `.bin`) upon completion. The project is packaged with a portable `.bat` launcher and portable `.exe`, documented, sanitized, and published to GitHub.

**Tech Stack:** Python 3.10+, Tkinter / ttk, PyInstaller, Node.js (WASM decrypt), Git, GitHub CLI (`gh`).

**Spec:** docs/superpowers/specs/2026-10-05-sketchfab-unlocker-gui-design.md

## Global Constraints
- Absolute requirement: NO comments or explanations in any code files (`#` comments or docstrings explaining code).
- Strict privacy: No personal machine paths (`C:\Users\Fasok\...`), Windows usernames, or credentials committed.
- Clean output enabled by default: remove `key.txt`, `file.osgjs`, `model_file.bin`, `model_file_wireframe.bin`, `textures_manifest.json` after conversion.
- GitHub target: public repository `wesiks/Sketchfab-Unlocker`.

---

### Task 1: Core Engine Optimization & Clean Output in `main.py`

**Files:**
- Modify: `main.py`
- Test: `test_clean.py`

**Interfaces:**
- Consumes: Existing `download_one` and `cleanup_work_dir` in `main.py`
- Produces: `download_one(..., clean_output: bool = True)` and `cleanup_work_dir(work_dir, keep, clean_output: bool = True)`

- [ ] **Step 1: Write test for clean output logic**
Write `test_clean.py` verifying that when `clean_output=True`, `key.txt`, `file.osgjs`, and intermediate `.bin` files are removed while `.gltf`, `textures/`, and `info.json` are retained.

- [ ] **Step 2: Run test to verify it fails**
Run: `py -3 test_clean.py`

- [ ] **Step 3: Update `main.py`**
Modify `cleanup_work_dir` and `download_one` in `main.py` to support `clean_output` (defaulting to True). Ensure zero comments in modified code.

- [ ] **Step 4: Run test to verify it passes**
Run: `py -3 test_clean.py`

- [ ] **Step 5: Clean up test file**
Remove `test_clean.py`.

---

### Task 2: High-End Desktop GUI (`gui.py`)

**Files:**
- Create: `gui.py`

**Interfaces:**
- Consumes: `download_one`, `check_tools`, `set_proxy`, `_WASM_DIR` from `main.py`
- Produces: Complete graphical desktop application for Windows

- [ ] **Step 1: Write `gui.py`**
Implement the dark-themed UI using Tkinter and TTK:
- Theme: Deep obsidian `#0B0E14`, card `#151922`, border `#252D3D`, accent `#6366F1`, hover `#4F46E5`, text `#F3F4F6`.
- Header with eyebrow badge "v2.0 Portable" and status indicators for Node.js and Decryptor.
- Multi-URL entry with "Вставить" (Paste) and "Очистить" (Clear) buttons.
- Settings row: Output path picker with browse dialog, "Очищать временные файлы (.key, .osgjs)" checkbox (checked by default), proxy input.
- Action row: "Скачать" button, progress bar, "Открыть папку" button.
- Log console for live output stream.
- Threaded execution so the UI never freezes during network operations.
- STRICT RULE: Zero comments in `gui.py`.

- [ ] **Step 2: Test GUI initialization**
Run: `py -3 -c "import gui; print('GUI module loaded successfully')"`

---

### Task 3: Portable Launcher Script & Executable Packaging

**Files:**
- Create: `start.bat`
- Create: `SketchfabUnlocker.bat`
- Build: `SketchfabUnlocker.exe` (via PyInstaller)

**Interfaces:**
- Consumes: `gui.py`, `main.py`, `tools/`
- Produces: 1-click portable launchers

- [ ] **Step 1: Create `start.bat` and `SketchfabUnlocker.bat`**
Create batch scripts to launch `gui.py` with `pythonw` without opening a terminal window, with fallback to `python` or `SketchfabUnlocker.exe`.

- [ ] **Step 2: Install PyInstaller and build portable EXE**
Install pyinstaller (`py -3 -m pip install pyinstaller`) and compile `gui.py` into `SketchfabUnlocker.exe` with `--noconsole`. Place `SketchfabUnlocker.exe` in the project root so it operates portably alongside `tools/`.

- [ ] **Step 3: Verify executable runs**
Test launch verification.

---

### Task 4: Documentation Customization for `wesiks`

**Files:**
- Modify: `README.md`
- Modify: `README.ru.md`

**Interfaces:**
- Consumes: Project features, GUI options, portable launcher
- Produces: Professional documentation for `wesiks/Sketchfab-Unlocker`

- [ ] **Step 1: Rewrite `README.md` in English**
Showcase Sketchfab Unlocker by `wesiks`, featuring GUI and Portable EXE, clean output mode, CLI instructions, and setup.

- [ ] **Step 2: Rewrite `README.ru.md` in Russian**
Showcase Sketchfab Unlocker от `wesiks`, с описанием запуска через GUI (EXE/батник), чистого режима, CLI и зависимостей.

---

### Task 5: Repository Sanitization & Git Initialization

**Files:**
- Modify: `.gitignore`
- Cleanup: `downloads/`

**Interfaces:**
- Consumes: Full workspace
- Produces: Clean, privacy-safe git working tree

- [ ] **Step 1: Update `.gitignore`**
Ensure `downloads/*` (except `!downloads/.gitkeep`), `build/`, `dist/`, `*.spec`, `*.pyc`, `__pycache__`, `tools/wasm/static_key.txt`, and personal logs are strictly ignored.

- [ ] **Step 2: Clean `downloads/` directory**
Remove all previously downloaded test models so that only `.gitkeep` remains.

- [ ] **Step 3: Scan for personal data**
Search workspace for any occurrences of user name `Fasok` or absolute paths and ensure none are present.

- [ ] **Step 4: Initialize git repository and stage files**
Configure safe directory and create initial clean commit.

---

### Task 6: Publish to GitHub (`wesiks/Sketchfab-Unlocker`)

**Files:**
- Remote: `https://github.com/wesiks/Sketchfab-Unlocker`

**Interfaces:**
- Consumes: Clean git repository
- Produces: Published GitHub repository

- [ ] **Step 1: Create repository via `gh`**
Run `gh repo create wesiks/Sketchfab-Unlocker --public --source=. --remote=origin --push`

- [ ] **Step 2: Verify repository status**
Verify repository page and remote tracking branch.
