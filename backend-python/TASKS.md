# GED-PME – Liste des tâches

## Module 1 : Fondations
- Environnement Python configuré
- Flask installé
- Dépendances définies dans requirements.txt
- Structure de projet établie

## Module 2 : Base de données
- MySQL 8.0 installé
- Base de données ged_pme créée
- Tables créées : users, entreprises, documents, categories, logs, notifications
- Relations définies (clés étrangères)

## Module 3 : API – 22 routes
- POST /register
- POST /login
- GET /profile
- GET /documents
- POST /documents
- PUT /documents/{id}
- DELETE /documents/{id}
- GET /documents/{id}/download
- GET /categories
- POST /categories
- PUT /categories/{id}
- DELETE /categories/{id}
- GET /users
- POST /admin/employes
- PUT /users/{id}/desactiver
- GET /api/dashboard/stats
- GET /api/pme/stats
- GET /api/admin-global/stats
- GET /api/admin-global/entreprises
- GET /api/admin-global/all-logs
- GET /api/admin-global/backup
- POST /api/admin-global/backup

## Module 4 : Sécurité JWT
- Génération de token JWT
- Middleware token_required
- Middleware role_required
- Hashage des mots de passe (Werkzeug)
- Expiration des tokens (24 heures)

## Module 5 : Upload et téléchargement
- Upload de fichiers avec vérification d'extension
- Sécurisation des noms de fichiers (secure_filename)
- Limitation de taille configurable
- Téléchargement avec contrôle d'accès

## Module 6 : Catégories
- Création d'une catégorie
- Lecture / liste des catégories
- Modification d'une catégorie
- Suppression d'une catégorie

## Module 7 : Logs et traçabilité
- Journalisation des actions
- Table logs en base de données
- Consultation des logs (admin global)
- Export CSV des logs

## Module 8 : Workflow documentaire
- Soumission d'un document (brouillon -> soumis)
- Validation d'un document (soumis -> valide)
- Rejet d'un document avec commentaire (soumis -> rejeté)
- Vérification des droits pour chaque transition

## Module 9 : Mode hors ligne (PWA)
- Service Worker (sw.js)
- Mise en cache des ressources statiques
- Page offline.html
- File d'attente (offline-queue.js)
- Synchronisation automatique au retour de connexion

## Module 10 : Sauvegarde
- Sauvegarde manuelle des données
- Export au format JSON
- Notification de succès ou échec

## Module 11 : Multi-entreprises
- Table entreprises
- Association user -> entreprise
- Isolation des données par entreprise
- Inscription d'une nouvelle entreprise

## Module 12 : Interface utilisateur (templates)
- Page de connexion (login.html)
- Page d'inscription entreprise (register_company.html)
- Page d'accueil publique (home.html)
- Templates responsive

## Module 13 : Dashboards

### Admin Global
- Dashboard avec statistiques globales
- Graphiques d'évolution (Chart.js)
- Gestion des entreprises (CRUD, activation/désactivation)
- Gestion des utilisateurs
- Consultation des logs
- Sauvegarde manuelle

### Admin PME (bug présent : création employé échoue)
- Dashboard avec statistiques entreprise
- Gestion des catégories (CRUD)
- Gestion des documents (liste, recherche)
- Corbeille (soft delete, restauration, suppression définitive, vider)
- Notifications in-app
- Export CSV
- Profil utilisateur
- Bug : création d'employé – request.user_entreprise_id non défini dans le middleware

### Dashboard Employé (bug présent : soumission instable)
- Dashboard personnel
- Upload de documents
- Consultation des documents
- Bug : soumission pour validation – échoue parfois
- Bug : liste des documents – affichage parfois vide

## Module 14 : OCR (non démarré)
- Intégration Tesseract à prévoir
- Extraction de texte depuis images et PDF
- Indexation du texte extrait
- Recherche full-text

## Module 15 : Tests terrain (non démarré)
- Déploiement dans des PME réelles
- Collecte des retours utilisateurs
- Correction des bugs remontés

## Module 16 : Documentation utilisateur (non démarrée)
- Guide d'installation
- Guide d'utilisation (Admin Global)
- Guide d'utilisation (Admin PME et Employé)

## Module 17 : Mémoire (en cours)
- Chapitres 1 et 2 rédigés
- Chapitres 3 à 5 à rédiger