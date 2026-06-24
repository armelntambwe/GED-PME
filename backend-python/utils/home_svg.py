"""Chargement des illustrations SVG pour la page d'accueil (inline HTML)."""
import os
import re

HOME_SVG_FILES = {
    'hero': 'hero-bg.svg',
    'ocr': 'feature-ocr.svg',
    'workflow': 'feature-workflow.svg',
    'offline': 'feature-offline.svg',
    'security': 'feature-security.svg',
    'whatsapp': 'feature-whatsapp.svg',
    'dashboard': 'feature-dashboard.svg',
    'role_employe': 'role-employe.svg',
    'role_admin_pme': 'role-admin-pme.svg',
    'role_admin_global': 'role-admin-global.svg',
    'showcase': 'showcase-server.svg',
}


def _unique_svg_ids(svg: str, prefix: str) -> str:
    ids = re.findall(r'\bid="([^"]+)"', svg)
    for old_id in set(ids):
        new_id = f'hl-{prefix}-{old_id}'
        svg = svg.replace(f'id="{old_id}"', f'id="{new_id}"')
        svg = svg.replace(f'url(#{old_id})', f'url(#{new_id})')
    return svg


def load_home_svgs(app) -> dict:
    base = os.path.join(app.root_path, 'static', 'img', 'home')
    out = {}
    for key, filename in HOME_SVG_FILES.items():
        path = os.path.join(base, filename)
        if not os.path.isfile(path):
            out[key] = ''
            continue
        with open(path, encoding='utf-8', errors='replace') as f:
            out[key] = _unique_svg_ids(f.read(), key)
    return out
