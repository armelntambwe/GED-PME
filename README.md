# GED-PME - Gestion Electronique de Documents pour PME

**Système de Gestion Electronique de Documents adapté aux Petites et Moyennes Entreprises en République Démocratique du Congo.**

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange.svg)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Table des matières

- [Aperçu](#aperçu)
- [État d'avancement](#état-davancement)
- [Fonctionnalités](#fonctionnalités)
- [Technologies utilisées](#technologies-utilisées)
- [Architecture](#architecture)
- [Installation](#installation)
- [Structure du projet](#structure-du-projet)
- [API Routes](#api-routes)
- [Bugs connus](#bugs-connus)
- [Contributions](#contributions)
- [Licence](#licence)

---

## 🚀 Aperçu

GED-PME est une solution de Gestion Electronique de Documents conçue spécifiquement pour les PME congolaises. Elle permet :

- 📄 **Gérer** vos documents de manière centralisée
- 🔒 **Sécuriser** l'accès avec une authentification JWT
- 🌐 **Travailler hors-ligne** grâce à l'architecture PWA
- 👥 **Isoler** les données par entreprise
- ✅ **Valider** les documents via un workflow structuré
- 📊 **Visualiser** des statistiques en temps réel
- 🔍 **Rechercher** dans les documents scannés grâce à l'OCR

---

## 📊 État d'avancement

| Module | Tâches | Statut | % |
|--------|--------|--------|---|
| Authentification & Sécurité | 100% | ✅ Terminé | 100% |
| Gestion des documents | 100% | ✅ Terminé | 100% |
| Workflow documentaire | 100% | ✅ Terminé | 100% |
| Multi-entreprises | 100% | ✅ Terminé | 100% |
| Mode hors-ligne (PWA) | 100% | ✅ Terminé | 100% |
| Notifications in-app | 100% | ✅ Terminé | 100% |
| OCR (Tesseract) | 100% | ✅ Terminé | 100% |
| Versionnage documentaire | 100% | ✅ Terminé | 100% |
| Dashboard Employé | 100% | ✅ Terminé | 100% |
| Dashboard Admin PME | 85% | ⚠️ En cours | 85% |
| Dashboard Admin Global | 90% | ⚠️ En cours | 90% |
| Tests terrain (3 PME) | 0% | 🔜 À venir | 0% |
| Documentation utilisateur | 0% | 🔜 À venir | 0% |
| **Moyenne générale** | **~98%** | | **98%** |

---

## ✨ Fonctionnalités

### Authentification & Sécurité
- ✅ Inscription et connexion sécurisées
- ✅ Tokens JWT (expiration 24h)
- ✅ 3 rôles : Admin Global, Admin PME, Employé
- ✅ Isolation des données par entreprise

### Gestion des documents
- ✅ Upload de fichiers (PDF, DOCX, JPG, PNG, TXT)
- ✅ Stockage sécurisé avec noms uniques
- ✅ Validation des formats (16 Mo max)
- ✅ Métadonnées (titre, description, date, auteur)
- ✅ Téléchargement sécurisé

### Workflow documentaire (7 états)
- ✅ Brouillon → En révision → Validé → Rejeté → Publié → Obsolète → Détruit
- ✅ Soumission par l'employé
- ✅ Validation/Rejet par l'admin (avec motif)
- ✅ Traçabilité complète des actions

### Fonctionnalités avancées
- ✅ OCR (Tesseract) : extraction de texte des images et PDF
- ✅ Versionnage : historique des modifications
- ✅ Mode hors-ligne (PWA avec Service Worker)
- ✅ Notifications in-app
- ✅ Audit et logs
- ✅ Corbeille (soft delete, restauration)
- ✅ Gestion multi-entreprises

### Interfaces
- ✅ Dashboard Employé
- ✅ Dashboard Administrateur PME
- ✅ Dashboard Administrateur Global

---

## 🛠️ Technologies utilisées

| Technologie | Version | Rôle |
|-------------|---------|------|
| **Python** | 3.11 | Langage principal |
| **Flask** | 2.3.3 | Framework web (API REST) |
| **MySQL** | 8.0 | Base de données |
| **SQLAlchemy** | 2.0 | ORM |
| **Alembic** | - | Migrations de schéma |
| **PyJWT** | 2.8.0 | Authentification par tokens |
| **Werkzeug** | 2.3.7 | Hashage des mots de passe |
| **Bootstrap** | 5.3 | Interface utilisateur |
| **Chart.js** | 4.4 | Graphiques dashboards |
| **Font Awesome** | 6.0 | Icônes interface |
| **Tesseract** | - | OCR (reconnaissance de texte) |
| **Git** | - | Versionnement |

---

## 🏗️ Architecture

L'application suit une architecture **4 tiers** :
┌─────────────────────────────────────────────────────────────────┐
│ TIER 1 : CLIENT (PWA) │
│ Bootstrap 5 / Service Worker / Chart.js │
└─────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ TIER 2 : API GATEWAY │
│ Nginx / Reverse Proxy │
└─────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ TIER 3 : APPLICATION (Flask) │
│ Authentification / Documents / Workflow / Notifications │
└─────────────────────────────────────────────────────────────────┘
│ │ │
▼ ▼ ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ TIER 4 : MySQL │ │ TIER 4 : Stockage│ │ TIER 4 : OCR │
│ (Données) │ │ (Fichiers) │ │ (Tesseract) │
└─────────────────┘ └─────────────────┘ └─────────────────┘

text

---

## 💻 Installation

### Prérequis
- Python 3.11+
- MySQL 8.0+
- Git

### Étapes

```bash
# 1. Cloner le dépôt
git clone https://github.com/armelntambwe/GED-PME.git
cd GED-PME/backend-python

# 2. Créer l'environnement virtuel
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Installer Tesseract OCR
# Windows : https://github.com/UB-Mannheim/tesseract/wiki
# Linux : sudo apt-get install tesseract-ocr tesseract-ocr-fra

# 5. Configurer MySQL
# - Créer une base de données 'ged_pme'
# - Configurer le fichier config.py

# 6. Initialiser la base de données
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# 7. Lancer les migrations Alembic (si nécessaire)
alembic upgrade head

# 8. Lancer le serveur
python app.py

# 9. Ouvrir le navigateur
# http://localhost:5000
📁 Structure du projet
text
backend-python/
├── app.py                      # Point d'entrée de l'application
├── config.py                   # Configuration (base de données, JWT)
├── extensions.py               # Initialisation SQLAlchemy, Alembic
├── requirements.txt            # Dépendances Python
│
├── models_sqlalchemy/          # Modèles ORM
│   ├── user.py
│   ├── document.py
│   ├── entreprise.py
│   ├── categorie.py
│   ├── version.py
│   ├── notification.py
│   └── log.py
│
├── routes/                     # Blueprints API
│   ├── authentification_routes.py
│   ├── document_routes.py
│   ├── admin_routes_orm.py
│   ├── user_routes.py
│   ├── category_routes.py
│   ├── notification_routes.py
│   └── company_routes.py
│
├── services/                   # Logique métier
│   ├── admin_service_orm.py
│   └── user_service.py
│
├── middleware/                 # Sécurité
│   └── auth.py                 # token_required, role_required
│
├── templates/                  # Interfaces HTML
│   ├── dashboard-employee.html
│   ├── dashboard-admin-pme.html
│   ├── dashboard-admin-global.html
│   ├── login.html
│   └── register_company.html
│
├── static/                     # Assets
│   ├── sw.js                   # Service Worker
│   └── offline-queue.js        # File d'attente offline
│
├── uploads/                    # Stockage des fichiers
├── backups/                    # Sauvegardes SQL
└── migrations/                 # Migrations Alembic
🌐 API Routes
Méthode	Endpoint	Description	Rôle requis
POST	/login	Authentification	Public
GET	/documents	Liste des documents	Employé
POST	/documents/upload	Upload d'un document	Employé
GET	/documents/<id>/download	Télécharger un document	Employé
PUT	/documents/<id>/soumettre	Soumettre un document	Employé
PUT	/documents/<id>/valider	Valider un document	Admin PME
PUT	/documents/<id>/rejeter	Rejeter un document	Admin PME
GET	/documents/corbeille	Voir la corbeille	Employé
PUT	/documents/<id>/restaurer	Restaurer un document	Admin PME
DELETE	/documents/<id>/effacer	Supprimer définitivement	Admin PME
GET	/api/pme/stats	Statistiques PME	Admin PME
GET	/api/admin-global/stats	Statistiques globales	Admin Global
GET	/notifications/all	Liste des notifications	Employé
PUT	/notifications/<id>/lire	Marquer une notification lue	Employé
🐛 Bugs connus
N°	Bug	Module	Priorité
1	Création employé (Admin PME) : l'employé créé n'apparaît pas dans la liste	Admin PME	Haute
2	Validation document : parfois ignorée	Admin PME	Haute
3	Exports CSV : page blanche ou erreur	Admin Global	Moyenne
4	Sauvegarde manuelle : ne fonctionne pas (mysqldump)	Admin Global	Moyenne
🤝 Contributions
Les contributions sont les bienvenues ! Voici comment contribuer :

Forker le projet

Créer une branche (git checkout -b feature/ma-fonctionnalite)

Commiter les changements (git commit -m 'Ajout d'une fonctionnalité')

Pusher la branche (git push origin feature/ma-fonctionnalite)

Ouvrir une Pull Request

📄 Licence
Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

👨‍💻 Auteur
Mbuyi Ntambwe Armel

GitHub : @armelntambwe

Projet : GED-PME

🙏 Remerciements
Université de Lubumbashi - Faculté des Sciences Informatiques

Encadreurs : Jordan Masakuna & Jonathan Mbemba