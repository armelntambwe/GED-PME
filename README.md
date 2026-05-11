# GED-PME - Gestion Electronique de Documents pour PME

![Version](https://img.shields.io/badge/version-1.0-blue)
![Python](https://img.shields.io/badge/python-3.10-green)
![Flask](https://img.shields.io/badge/flask-2.3-lightgrey)
![MySQL](https://img.shields.io/badge/mysql-8.0-orange)
![Statut](https://img.shields.io/badge/statut-85%25-brightgreen)

**Systeme de Gestion Electronique de Documents adapte aux Petites et Moyennes Entreprises en Republique Democratique du Congo.**

---

## Etat d'avancement

| Module | Taches | Statut | % |
|--------|--------|--------|---|
| Modules 1-13 | 100/110 taches | Termine | 85% |
| Module 14 (OCR) | 0% | En cours | 0% |
| Module 15 (Tests terrain) | 0% | A venir | 0% |
| Module 16 (Documentation) | 0% | A venir | 0% |
| Module 17 (Mmoire) | 0% | A venir | 0% |

---

## Fonctionnalites deja realisees

### Authentification & Securite
- Inscription et connexion securisees
- Tokens JWT (expiration 24h)
- 3 roles : Admin Global, Admin PME, Employe
- Isolation des donnees (employe voit ses docs)

### Gestion des documents
- Upload de fichiers (PDF, DOCX, JPG, PNG, TXT)
- Stockage securise avec noms uniques
- Validation des formats et taille (16 Mo max)
- Metadonnees (titre, description, date, auteur)
- Telechargement des fichiers (`GET /documents/{id}/download`)

### Workflow documentaire
- Brouillon -> Soumis -> Valide / Rejete
- Soumission par l'employe
- Validation/Rejet par l'admin (avec commentaire)
- Traabilite (qui a fait quoi, quand)

### Organisation
- Gestion des categories (CRUD)
- Logs et tracabilite complete
- Multi-entreprises (isolation des donnees)

---

## Fonctionnalites en cours de developpement

| Fonctionnalite | Avancement | Priorite |
|----------------|------------|----------|
| Mode hors-ligne (PWA) | 100% | Termine |
| Sauvegarde automatique | 100% | Termine |
| Interface utilisateur | 90% | Finalisation |
| Dashboard Admin Global | 90% | Finalisation |
| OCR (Tesseract) | 0% | Semaine 1 |
| Tests terrain (3 PME) | 0% | Semaine 3 |
| Documentation utilisateur | 0% | Semaine 4 |

---

## Technologies utilisees

| Technologie | Version | Role |
|-------------|---------|------|
| **Flask** | 2.3.3 | Framework web (API REST) |
| **MySQL** | 8.0 | Base de donnees |
| **PyJWT** | 2.8.0 | Authentification par tokens |
| **Werkzeug** | 2.3.7 | Hashage des mots de passe |
| **Chart.js** | 4.4 | Graphiques dashboards |
| **Font Awesome** | 6.0 | Icones interface |

---

## Installation

```bash
# 1. Cloner le depot
git clone https://github.com/armelntambwe/GED-PME.git
cd GED-PME/backend-python

# 2. Installer l'environnement virtuel
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Installer les dependances
pip install -r requirements.txt

# 4. Configurer MySQL (XAMPP)
# - Creer une base 'ged_pme'

# 5. Initialiser la base
python database/init_db.py

# 6. Lancer le serveur
python app.py
