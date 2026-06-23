# GED-PME

Application web de **Gestion Électronique de Documents** pour PME : multi-entreprises, workflow de validation, recherche OCR et espaces par rôle.

**Dépôt :** [github.com/armelntambwe/GED-PME](https://github.com/armelntambwe/GED-PME)

---

## Fonctionnalités

- Multi-entreprises (NIF, RCCM, logo, secteur)
- Rôles : Admin global · Admin PME · Employé
- Workflow : brouillon → révision → validé / rejeté → publié → obsolète → détruit
- Aperçu PDF, images, texte, vidéo, audio, DOCX
- OCR (Tesseract), versionnage, corbeille, catégories
- Mode hors-ligne (PWA), notifications, alertes WhatsApp, 2FA (TOTP)

---

## Stack

Python 3.10+ · Flask · MySQL 8 · SQLAlchemy · JWT · Bootstrap 5 · Chart.js

---

## Installation

**Prérequis :** Python 3.10+, MySQL 8, [Tesseract](https://github.com/tesseract-ocr/tesseract) (optionnel)

```bash
git clone https://github.com/armelntambwe/GED-PME.git
cd GED-PME/backend-python

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

pip install -r requirements.txt
copy .env.example .env         # puis adapter APP_BASE_URL, MySQL…
```

Configurer MySQL dans `config.py`, puis :

```bash
python app.py
```

→ [http://localhost:5000](http://localhost:5000)

| Page | URL |
|------|-----|
| Accueil | `/` |
| Inscription entreprise | `/register-company` |
| Connexion | `/login` |
| Employé | `/dashboard-employee` |
| Admin PME | `/dashboard-admin-pme` |
| Admin global | `/dashboard-admin-global` |

---

## Configuration

Copier `backend-python/.env.example` vers `.env` :

```env
APP_BASE_URL=http://localhost:5000
WHATSAPP_ENABLED=true
WHATSAPP_PROVIDER=callmebot
DEFAULT_PHONE_PREFIX=+243
```

WhatsApp (CallMeBot) : chaque utilisateur active son numéro et sa clé API dans **Mon profil**.

---

## Structure

```
GED-PME/
├── README.md
└── backend-python/
    ├── app.py
    ├── routes/          # API REST
    ├── services/        # Logique métier
    ├── models_sqlalchemy/
    ├── templates/       # Interface web
    ├── static/          # CSS, JS, PWA
    └── utils/           # OCR, WhatsApp, schéma DB…
```

---

## Auteur

**Mbuyi Ntambwe Armel** — [@armelntambwe](https://github.com/armelntambwe)

Université de Lubumbashi — Faculté des Sciences Informatiques
