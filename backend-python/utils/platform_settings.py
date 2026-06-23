"""Paramètres plateforme persistés (mode maintenance, etc.)."""
import json
import os

_SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'platform_settings.json')
_DEFAULTS = {'maintenance_mode': False, 'maintenance_message': 'Maintenance en cours. Réessayez plus tard.'}


def _ensure_dir():
    d = os.path.dirname(_SETTINGS_FILE)
    if not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)


def load_platform_settings() -> dict:
    _ensure_dir()
    if not os.path.isfile(_SETTINGS_FILE):
        return dict(_DEFAULTS)
    try:
        with open(_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        out = dict(_DEFAULTS)
        out.update({k: data[k] for k in _DEFAULTS if k in data})
        return out
    except Exception:
        return dict(_DEFAULTS)


def save_platform_settings(updates: dict) -> dict:
    current = load_platform_settings()
    for key in _DEFAULTS:
        if key in updates:
            current[key] = updates[key]
    _ensure_dir()
    with open(_SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(current, f, ensure_ascii=False, indent=2)
    return current


def is_maintenance_mode() -> bool:
    return bool(load_platform_settings().get('maintenance_mode'))
