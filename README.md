\# 📁 GED-PME



Système de Gestion Électronique de Documents adapté aux Petites et Moyennes Entreprises en République Démocratique du Congo.



!\[Version](https://img.shields.io/badge/version-1.0-blue)

!\[Python](https://img.shields.io/badge/python-3.10-green)

!\[Flask](https://img.shields.io/badge/flask-2.3-lightgrey)

!\[MySQL](https://img.shields.io/badge/mysql-8.0-orange)

!\[Statut](https://img.shields.io/badge/statut-en%20développement-yellow)



---



\## ✅ \*\*Fonctionnalités déjà réalisées\*\*



\### 🔐 \*\*Authentification \& Sécurité\*\*

\- ✅ Inscription et connexion sécurisées

\- ✅ Tokens JWT (expiration 24h)

\- ✅ 3 rôles : Admin Global, Admin PME, Employé

\- ✅ Isolation des données (employé voit ses docs)



\### 📄 \*\*Gestion des documents\*\*

\- ✅ Upload de fichiers (PDF, DOCX, JPG, PNG, TXT)

\- ✅ Stockage sécurisé avec noms uniques

\- ✅ Validation des formats et taille (16 Mo max)

\- ✅ Métadonnées (titre, description, date, auteur)



\### 🔄 \*\*Workflow documentaire\*\*

\- ✅ Brouillon → Soumis → Validé / Rejeté

\- ✅ Soumission par l'employé

\- ✅ Validation/Rejet par l'admin (avec commentaire)

\- ✅ Traçabilité (qui a fait quoi, quand)



---



\## 🚧 \*\*Fonctionnalités en cours de développement\*\*



\- ⏳ Téléchargement des fichiers (`GET /documents/{id}/download`)

\- ⏳ Gestion des catégories (CRUD)

\- ⏳ Logs et traçabilité complète

\- ⏳ Mode hors-ligne (stockage local)

\- ⏳ Sauvegarde automatique

\- ⏳ Interface utilisateur (frontend)



---



\## 🛠️ \*\*Technologies utilisées\*\*



| Technologie | Version | Rôle |

|-------------|---------|------|

| \*\*Flask\*\* | 2.3.3 | Framework web (API REST) |

| \*\*MySQL\*\* | 8.0 | Base de données |

| \*\*PyJWT\*\* | 2.8.0 | Authentification par tokens |

| \*\*Werkzeug\*\* | 2.3.7 | Hashage des mots de passe |



---



\## 🚀 \*\*Installation\*\*



```bash

\# 1. Cloner le dépôt

git clone https://github.com/armelntambwe/GED-PME.git

cd GED-PME/backend-python



\# 2. Installer l'environnement virtuel

python -m venv venv

venv\\Scripts\\activate  # Windows

pip install -r requirements.txt



\# 3. Configurer MySQL (XAMPP)

\# - Créer une base 'ged\_pme'



\# 4. Initialiser la base

python database/init\_db.py



\# 5. Lancer le serveur

python app.py

```



---



\## 📊 \*\*Routes API disponibles\*\*



| Méthode | Route | Description |

|---------|-------|-------------|

| `POST` | `/register` | Inscription |

| `POST` | `/login` | Connexion (reçoit token) |

| `POST` | `/documents/upload` | Upload fichier |

| `GET` | `/documents` | Liste documents |

| `PUT` | `/documents/{id}/soumettre` | Soumettre |

| `PUT` | `/documents/{id}/valider` | Valider (admin) |

| `PUT` | `/documents/{id}/rejeter` | Rejeter (admin) |



---



\## 👨‍💻 \*\*Auteur\*\*



\*\*Armel NTAMBWE\*\*  

Étudiant en Licence 4 - Génie Logiciel  

Projet de mémoire : \*Conception et déploiement d'une GED adaptée aux PME locales en RDC\*



---



\*Document mis à jour le : 7 Mars 2026\*

