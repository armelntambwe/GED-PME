# GED-PME

Application web de **Gestion Électronique de Documents** pour les PME : multi-entreprises, workflow de validation, OCR, tableaux de bord par rôle et déploiement sur serveur local (LAN).

**Dépôt :** [github.com/armelntambwe/GED-PME](https://github.com/armelntambwe/GED-PME)

Projet académique — **Université Nouveaux Horizons**, Lubumbashi, RDC (2026).

---

## Fonctionnalités

### Cœur métier
- **Multi-PME** : inscription avec NIF, RCCM, logo ; isolation stricte des données par entreprise
- **3 rôles** : admin global (supervision) · admin PME · employé
- **Workflow documentaire** : brouillon → révision → validé / rejeté → publié → obsolète → détruit
- **Catégories** propres à chaque entreprise (CRUD admin PME)
- **Corbeille** : soft delete, restauration, suppression définitive
- **Versionnage** des documents et journal d'audit

### Recherche & fichiers
- Upload PDF, images, Office, CSV, etc.
- **OCR Tesseract** (PDF et images scannées) + recherche full-text
- **Aperçu** : PDF, images, texte, vidéo, audio, DOCX (Mammoth), XLSX/CSV

### Sécurité
- Authentification **JWT** (session 24 h), mots de passe **bcrypt**
- **2FA TOTP** (Google / Microsoft Authenticator) sur tous les rôles
- Contrôle d'accès par rôle et par entreprise

### Contexte PME / RDC
- **PWA hors ligne** (espace employé) : file d'attente locale + synchronisation
- **Alertes WhatsApp** via CallMeBot (configurable dans le profil)
- **Interface bilingue FR / EN** (accueil, connexion, inscription)
- **Sauvegarde SQL** manuelle (admin PME et admin global)
- **Mode maintenance** (admin global)

### Tableaux de bord
| Rôle | Capacités principales |
|------|------------------------|
| **Employé** | Upload, soumission workflow, docs publiés, historique, PWA |
| **Admin PME** | Validation/rejet, employés, catégories, stats, export, backup |
| **Admin global** | Onboarding PME, vue documents (lecture seule), logs, export CSV, maintenance |

---

## Stack technique

Python 3.10+ · Flask · MySQL 8 · SQLAlchemy · Flask-Migrate · JWT · Bootstrap 5 · Chart.js · Tesseract OCR · PWA (Service Worker)

---

## Installation

**Prérequis :** Python 3.10+, MySQL 8, [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (recommandé pour l'OCR)

```bash
git clone https://github.com/armelntambwe/GED-PME.git
cd GED-PME/backend-python

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

pip install -r requirements.txt
copy .env.example .env         # Windows — adapter MySQL, APP_BASE_URL…
# cp .env.example .env         # Linux / macOS
```

Configurer la connexion MySQL dans `config.py`, créer la base `ged_pme`, puis :

```bash
python app.py
```

→ [http://localhost:5000](http://localhost:5000)

### Pages web

| Page | URL |
|------|-----|
| Accueil | `/` |
| Inscription PME | `/register-company` |
| Connexion | `/login` |
| Guide utilisateur | `/guide` |
| Dashboard employé | `/dashboard-employee` |
| Dashboard admin PME | `/dashboard-pme` |
| Dashboard admin global | `/dashboard-admin-global` |
| Langue | `/lang/fr` ou `/lang/en` |

---

## Configuration

Copier `backend-python/.env.example` vers `.env` :

```env
APP_BASE_URL=http://localhost:5000
WHATSAPP_ENABLED=true
WHATSAPP_PROVIDER=callmebot
DEFAULT_PHONE_PREFIX=+243
```

**WhatsApp (CallMeBot)** : chaque utilisateur configure son numéro (+243…) et sa clé API personnelle dans **Mon profil**.

**Numérisation** : scan externe (appareil ou mobile) → export PDF/image → upload dans GED-PME → OCR automatique côté serveur.

---

## Structure du projet

```
GED-PME/
├── README.md
└── backend-python/
    ├── app.py                 # Point d'entrée Flask
    ├── config.py
    ├── routes/                # API REST (documents, admin, users…)
    ├── services/              # Logique métier (workflow, OCR, backup…)
    ├── models_sqlalchemy/     # Modèles ORM
    ├── templates/             # Pages HTML (dashboards, accueil, guide)
    ├── translations/          # i18n FR / EN
    ├── static/                # CSS, JS, PWA (sw.js), illustrations
    ├── utils/                 # OCR, WhatsApp, i18n, schéma DB
    └── uploads/               # Fichiers documentaires
```

---

## Documentation

- **Guide utilisateur intégré** : `/guide` (employé, admin PME, admin global)
- **Liste des modules** : `backend-python/TASKS.md`

---

## Auteur

**Mbuyi Ntambwe Armel** — [@armelntambwe](https://github.com/armelntambwe)

Université **Nouveaux Horizons** — Lubumbashi, République Démocratique du Congo  
Travail de fin d'études — Génie informatique / GED — 2026
