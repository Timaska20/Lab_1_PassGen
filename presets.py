# src/presets.py
import json
from pathlib import Path
from typing import Dict, Any

PRESETS_DIR = Path.cwd() / "presets"
PRESETS_DIR.mkdir(exist_ok=True)

def save_preset(name: str, settings: Dict[str, Any]) -> Path:
    # Normalize name (strip extension if given)
    fname = PRESETS_DIR / (name if name.endswith(".json") else f"{name}.json")
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
    return fname

def load_preset(path) -> Dict[str, Any]:
    p = Path(path)
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def list_presets():
    return list(PRESETS_DIR.glob("*.json"))
