# Password Generator (Python, ttkbootstrap)
Modern GUI password generator with customizable alphabet, presets, entropy display, and optional zxcvbn scoring.

## Features
- Choose length (4..128), groups (A–Z, a–z, 0–9, symbols), and/or custom alphabet.
- "Use ONLY custom alphabet" toggle to replace groups.
- Entropy estimation (bits).
- Save / load presets (JSON).
- Copy / Clear / Export to file.
- Optional zxcvbn strength score popup (if installed).

## Requirements (recommended, Variant B)
```bash
python -m venv venv
# Windows PowerShell
./venv/Scripts/Activate.ps1
# macOS/Linux
source venv/bin/activate

pip install -U pip
pip install -r requirements.txt
```
> If you don't want zxcvbn or pyperclip, you can remove them from requirements.txt — the app will still run.
> `tkinter` comes with most Python distributions (on some Linux distros install `python3-tk`).

## Run
From project root:
```bash
python -m src.app
# or
python app.py
```

## Presets
Presets are saved to the `presets/` directory next to `src/` by default.
