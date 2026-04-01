# DAV to MP4 Converter

A simple GUI tool for converting Hikvision `.dav` surveillance footage to `.mp4` files. Works on Windows, Mac, and Linux.

![Python](https://img.shields.io/badge/Python-3.9+-blue) ![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-lightgrey) ![License](https://img.shields.io/badge/License-MIT-green)

## Features

- Convert single files or entire folders of `.dav` files
- Fast stream copy when possible, automatic re-encode fallback
- Progress tracking and conversion log
- Choose a custom output directory or save alongside originals

## Usage

### Windows (no Python needed)

Download `DAV Converter.exe` from the [latest release](../../actions) under **Actions > Build Windows EXE > Artifacts**, and double-click it. FFmpeg is bundled — no extra installs needed.

### Mac / Linux

Requires FFmpeg: `brew install ffmpeg` (Mac) or `sudo apt install ffmpeg` (Linux).

```bash
pip3 install -r requirements.txt
python3 convert_dav_gui.py
```

## Building the EXE Yourself

The GitHub Actions workflow automatically builds a Windows `.exe` on every push to `main`. You can also trigger it manually from the **Actions** tab.

To build locally on Windows:

```bash
pip install -r requirements.txt
pyinstaller --onefile --windowed --name "DAV Converter" --add-data "logo.png;." convert_dav_gui.py
```

The output will be in the `dist/` folder.
