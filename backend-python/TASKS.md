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
- Relations définies

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
- Hashage des mots de passe
- Expiration des tokens (24h)

## Module 5 : Upload et téléchargement
- Upload avec vérification d'extension
- Sécurisation des noms de fichiers
- Limitation de taille
- Téléchargement avec contrôle d'accès

## Module 6 : Catégories
- Création d'une catégorie
- Lecture / liste des catégories
- Modification d'une catégorie
- Suppression d'une catégorie

## Module 7 : Logs
- Journalisation des actions
- Table logs en base de données
- Consultation des logs
- Export CSV des logs

## Module 8 : Workflow
- Soumission (brouillon -> soumis)
- Validation (soumis -> valide)
- Rejet avec commentaire (soumis -> rejeté)
- Vérification des droits pour chaque transition

## Module 9 : Mode hors ligne PWA
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

## Module 12 : Interface utilisateur
- Page de connexion (login.html)
- Page d'inscription entreprise (register_company.html)
- Page d'accueil publique (home.html)
- Templates responsive

## Module 13 : Dashboards

### Admin Global
- Dashboard avec statistiques globales
- Graphiques d'évolution (Chart.js)
- Gestion des entreprises (CRUD)
- Gestion des utilisateurs
- Consultation des logs
- Sauvegarde manuelle

### Admin PME
- Dashboard avec statistiques entreprise
- Gestion des catégories (CRUD)
- Gestion des documents (liste, recherche)
- Corbeille (soft delete, restauration, suppression définitive, vider)
- Notifications in-app
- Export CSV
- Profil utilisateur

### Dashboard Employé
- Dashboard personnel
- Upload de documents
- Consultation des documents

## Module 14 : OCR
- Intégration Tesseract
- Extraction de texte depuis images et PDF
- Indexation du texte extrait
- Recherche full-text

## Module 15 : Tests terrain
- Déploiement dans des PME réelles
- Collecte des retours utilisateurs
- Correction des bugs remontés

## Module 16 : Documentation utilisateur
- Guide d'installation
- Guide d'utilisation (Admin Global)
- Guide d'utilisation (Admin PME et Employé)

## Module 17 : Mémoire
- Rédaction chapitre 1 (Introduction)
- Rédaction chapitre 2 (État de l'art)
- Rédaction chapitre 3 (Méthodologie)
- Rédaction chapitre 4 (Implémentation)
- Rédaction chapitre 5 (Résultats, tests et perspectives)
- Captures d'écran
- Relecture et corrections