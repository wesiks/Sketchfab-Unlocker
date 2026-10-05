# Sketchfab Unlocker

[![Version](https://img.shields.io/badge/version-2.0-indigo.svg)](https://github.com/wesiks/Sketchfab-Unlocker)
[![Author](https://img.shields.io/badge/author-wesiks-blue.svg)](https://github.com/wesiks)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/wesiks/Sketchfab-Unlocker)
[![Interface](https://img.shields.io/badge/interface-GUI%20%7C%20CLI-success.svg)](https://github.com/wesiks/Sketchfab-Unlocker)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Language / Язык:** **English** | [Русский](README.ru.md)

**Sketchfab Unlocker** by **wesiks** is a utility designed to download and unlock public 3D models from [Sketchfab](https://sketchfab.com) in **glTF 2.0** format with high-resolution textures.

- **No** Sketchfab account required  
- **No** API keys or authentication tokens needed  
- Works even for models without an official Download button  
- **Desktop GUI** with modern dark interface  
- **Portable 1-Click Launchers** (`SketchfabUnlocker.exe`, `start.bat`, `SketchfabUnlocker.bat`)  
- **Clean Output Mode** (automatically purges temporary decryption artifacts)  
- Multi-platform CLI for Windows, Linux, and macOS  
- Docker support for automated containerized environments  

---

## Table of Contents

1. [Features](#features)
2. [Quick Start: Windows Desktop GUI](#quick-start-windows-desktop-gui)
3. [Quick Start: CLI](#quick-start-cli)
4. [Quick Start: Docker](#quick-start-docker)
5. [Clean Output Mode](#clean-output-mode)
6. [CLI Usage and Options](#cli-usage-and-options)
7. [Requirements](#requirements)
8. [Where Files Are Saved](#where-files-are-saved)
9. [How It Works](#how-it-works)
10. [Troubleshooting & FAQ](#troubleshooting--faq)
11. [Project Layout](#project-layout)
12. [Legal Disclaimer](#legal-disclaimer)
13. [License & Credits](#license--credits)

---

## Features

| Feature | Description |
|---|---|
| **Modern Desktop GUI** | Standalone dark-mode graphical user interface with clipboard paste, real-time logs, and folder open |
| **Portable Launch** | Run immediately via `SketchfabUnlocker.exe`, `start.bat`, or `SketchfabUnlocker.bat` |
| **Public Model Download** | Unlock models using standard web URLs or 32-character hexadecimal UIDs |
| **No Download Button Required** | Accesses the public 3D viewer mesh stream |
| **Clean Output Mode** | Deletes temporary decrypt files (`key.txt`, `file.osgjs`, `.bin` artifacts) automatically |
| **glTF 2.0 Output** | Full glTF mesh output with external buffers and textures, ready for Blender, Unreal, and Unity |
| **Batch Processing** | Download multiple URLs in a single run |
| **Proxy Support** | Pass HTTP/HTTPS or SOCKS proxies |
| **Cross-Platform** | Native Windows support, plus Linux, macOS, and Docker |

**Unsupported:**
- Private or password-protected models
- Paid store models
- Direct account login

---

## Quick Start: Windows Desktop GUI

### Option A: Portable Standalone Executable
1. Download the repository or release archive from [wesiks/Sketchfab-Unlocker](https://github.com/wesiks/Sketchfab-Unlocker).
2. Launch `SketchfabUnlocker.exe`.
3. Paste your Sketchfab model URL into the input field.
4. Click **Скачать модель** (Download Model).
5. When complete, click **Открыть папку** (Open Folder) to access your clean glTF model and textures.

### Option B: Batch Launcher
Double-click `start.bat` or `SketchfabUnlocker.bat`. The launcher automatically locates the standalone executable or system Python installation and starts the interface.

---

## Quick Start: CLI

### 1. Clone the repository
```bash
git clone https://github.com/wesiks/Sketchfab-Unlocker.git
cd Sketchfab-Unlocker
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Verify tools
```bash
python main.py --check-tools
```

### 4. Download a model
```bash
python main.py "https://sketchfab.com/3d-models/your-model-name-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

The model will be downloaded, decrypted, converted to glTF, and cleaned in the `downloads/` directory.

---

## Quick Start: Docker

Docker includes Python, Node.js, Wine, and conversion tools out of the box.

### 1. Build container image
```bash
docker compose build
```

### 2. Run download
```bash
docker compose run --rm downloader "https://sketchfab.com/3d-models/your-model-url"
```

Models appear in `./downloads/` on the host machine.

---

## Clean Output Mode

By default, **Clean Output Mode** is enabled in both the GUI and the CLI.

During extraction and conversion, several intermediate files are created:
- `key.txt` and `key2.txt` (encryption keys extracted from stream)
- `file.osgjs` (intermediate OSGJS scene graph)
- `model_file.bin` and `model_file_wireframe.bin` (raw binary buffers)
- `textures_manifest.json` (temporary texture map)

When Clean Output Mode finishes, all intermediate files are purged automatically. Only the final production-ready assets remain:
- `Model_Name.gltf`
- Referenced `.bin` geometry buffers
- `textures/` directory
- `info.json` (metadata, title, author, source URL)

### Keeping Intermediate Files
If you want to keep raw decryption files for debugging:
- **CLI**: Pass the `--no-clean` flag:
  ```bash
  python main.py --no-clean "https://sketchfab.com/3d-models/..."
  ```
- **GUI**: Uncheck the **Очищать временные файлы** option.

---

## CLI Usage and Options

```text
python main.py [OPTIONS] [URL_OR_UID ...]
```

| Option | Description |
|---|---|
| `urls` | One or more Sketchfab model URLs or 32-character UIDs |
| `-o`, `--output DIR` | Target output directory (default: `downloads/`) |
| `--proxy PROXY_URL` | HTTP, HTTPS, or SOCKS proxy address |
| `--no-clean` | Preserve temporary decryption and conversion files |
| `--check-tools` | Verify Node.js, WASM worker, Wine, and conversion binaries |
| `-q`, `--quiet` | Suppress non-essential banner output |
| `-h`, `--help` | Show help and argument summary |

### CLI Examples

Download a single model:
```bash
python main.py "https://sketchfab.com/3d-models/example-0123456789abcdef0123456789abcdef"
```

Download by 32-character UID:
```bash
python main.py 0123456789abcdef0123456789abcdef
```

Download multiple models in one run:
```bash
python main.py URL1 URL2 URL3
```

Specify custom output directory:
```bash
python main.py -o ./my_models "https://sketchfab.com/3d-models/..."
```

Download through a proxy:
```bash
python main.py --proxy "http://127.0.0.1:8080" "https://sketchfab.com/3d-models/..."
```

Keep raw decryption dumps:
```bash
python main.py --no-clean "https://sketchfab.com/3d-models/..."
```

---

## Requirements

### Windows
- **Node.js 18+**: Required for `.binz` WebAssembly decryption worker. Download from [nodejs.org](https://nodejs.org/).
- **Python 3.10+**: Only required if running from source rather than the compiled `SketchfabUnlocker.exe`.

### Linux
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nodejs wine64
```
Wine is used to run `osgconv.exe` for optimal glTF generation. If Wine is not present, a built-in pure Python converter serves as fallback.

### macOS
```bash
brew install python node wine-stable
```

---

## Where Files Are Saved

```text
downloads/
└── Model_Name-01234567/
    ├── Model_Name.gltf
    ├── Model_Name.bin
    ├── textures/
    │   ├── texture_0.png
    │   └── texture_1.png
    └── info.json
```

### Importing into Blender
1. Open Blender.
2. Select **File > Import > glTF 2.0 (.glb / .gltf)**.
3. Select `Model_Name.gltf` from the output directory.

---

## How It Works

1. **Metadata Resolution**: Queries the public Sketchfab viewer page and parses the scene manifest.
2. **Buffer Ingestion**: Downloads encrypted `.binz` chunks and scene definition files from the CDN.
3. **WASM Decryption**: Node.js executes the WebAssembly decryptor using dynamic per-model keys combined with live static keys extracted from the viewer runtime.
4. **glTF Conversion**: Converts OSGJS data to standard glTF 2.0 with geometry buffers.
5. **Texture Retrieval**: Queries the public texture endpoint and downloads all available texture maps.
6. **Clean Purge**: Cleans intermediate artifacts unless `--no-clean` is specified.

---

## Troubleshooting & FAQ

### Node.js is missing
Install Node.js 18 or newer from [nodejs.org](https://nodejs.org/) and ensure `node` is available in your system PATH. Node.js is required to execute the WASM decryption worker.

### Missing tools in `tools/`
If the binaries in `tools/` are missing, run:
```bash
python setup_tools.py
```

### Model fails to download
- Verify the model is publicly accessible in a web browser without being logged in.
- Store models or private password-protected links cannot be downloaded.
- Run `python main.py --check-tools` to ensure your local environment is correctly configured.

---

## Project Layout

| File / Directory | Description |
|---|---|
| `gui.py` | Desktop graphical user interface |
| `main.py` | Core engine and CLI interface |
| `osgjs_convert.py` | Python OSGJS to glTF converter fallback |
| `textures.py` | Texture fetching pipeline |
| `setup_tools.py` | Tool downloader and verification |
| `start.bat` | Windows launcher script |
| `SketchfabUnlocker.bat` | Windows branded launcher script |
| `SketchfabUnlocker.exe` | Standalone Windows executable |
| `requirements.txt` | Python package dependencies |
| `Dockerfile` | Container definition |
| `docker-compose.yml` | Docker compose configuration |
| `tools/` | WASM decryptor and conversion binaries |
| `downloads/` | Default output directory |
| `README.md` | English documentation |
| `README.ru.md` | Russian documentation |

---

## Legal Disclaimer

This tool is designed for educational and personal interoperability purposes, accessing public 3D viewer data in the same manner as a standard web browser.
- Respect copyright and author licenses listed on model pages.
- Do not use for commercial redistribution or bypassing paid assets.
- Authors assume no liability for misuse of this software.

---

## License & Credits

- Software authored by **wesiks** ([GitHub](https://github.com/wesiks)).
- Licensed under the **MIT License**. See [LICENSE](LICENSE) for details.
- Community credit to contributors in the 3D preservation ecosystem.
