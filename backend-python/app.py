# app.py - Version nettoyée sans doublons
from flask import Flask, send_from_directory, render_template, request, jsonify, send_file
from config import Config
from utils.db import get_db, test_connection
from middleware.auth import token_required, role_required, get_current_user
from werkzeug.security import generate_password_hash, check_password_hash
from utils.jwt_manager import generer_token
from utils.schema_init import ensure_schema
from utils.ocr_helper import extract_text_from_file
from services.indexation_service import IndexationService
from services.version_service import VersionService
from services.archivage_service import ArchivageService
from extensions import db, migrate

# Importer les modèles SQLAlchemy
from models_sqlalchemy import Entreprise, User, Document, Categorie, Log, VersionDocument, Notification

# Routes imports
from routes.authentification_routes import register_authentification_routes
from routes.document_routes import register_document_routes
from routes.admin_routes_orm import register_admin_routes_orm
from routes.user_routes import register_user_routes
from routes.category_routes import register_category_routes
from routes.notification_routes import register_notification_routes
from routes.company_routes import register_company_routes

# Services imports
from services.admin_service_orm import AdminService
from services.user_service import UserService

import os
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

# Initialisation SQLAlchemy / Flask-Migrate
db.init_app(app)
migrate.init_app(app, db)
ensure_schema(app)

with app.app_context():
    try:
        archived = ArchivageService.run_auto_archivage()
        if archived:
            print(f"Archivage automatique: {archived} document(s) traité(s)")
    except Exception as e:
        print(f"Archivage automatique ignoré: {e}")

# Test de connexion MySQL
print("Verification MySQL...")
success, message = test_connection()
print(f"{message}" if success else f"{message}")

# ============================================
# ENREGISTREMENT DES ROUTES (SANS DOUBLONS)
# ============================================
register_authentification_routes(app)
register_document_routes(app)
register_admin_routes_orm(app)
register_user_routes(app)
register_category_routes(app)
register_notification_routes(app)
register_company_routes(app)

# ==============================
# FICHIERS STATIQUES (PWA)
# ==============================
@app.route('/sw.js')
def serve_sw():
    resp = send_from_directory('static', 'sw.js')
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    return resp

@app.route('/offline.html')
def serve_offline():
    return send_from_directory('static', 'offline.html')

@app.route('/offline-queue.js')
def serve_offline_queue():
    return send_from_directory('static', 'offline-queue.js')

# ==============================
# PAGES HTML
# ==============================
@app.route('/')
def index():
    return render_template('home.html')


@app.route('/api/public/stats', methods=['GET'])
def public_stats():
    """Statistiques publiques pour la page d'accueil."""
    try:
        from models_sqlalchemy import Entreprise, User, Document
        stats = {
            'entreprises': Entreprise.query.count(),
            'utilisateurs': User.query.filter_by(actif=True).count(),
            'documents': Document.query.filter(Document.supprime_le.is_(None)).count(),
        }
        return jsonify({'success': True, 'stats': stats}), 200
    except Exception as e:
        return jsonify({'success': True, 'stats': {'entreprises': 0, 'utilisateurs': 0, 'documents': 0}}), 200


@app.route('/api/pme/evolution', methods=['GET'])
@token_required
@role_required(['admin_pme'])
def pme_evolution():
    try:
        from models.document import Document as DocWrapper
        data = DocWrapper.get_evolution(request.user_entreprise_id, weeks=8)
        return jsonify({'success': True, 'evolution': data}), 200
    except Exception as e:
        return jsonify({'success': False, 'evolution': []}), 200


@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register-company')
def register_company_page():
    return render_template('register_company.html')

@app.route('/dashboard-admin-global')
def dashboard_admin_global():
    return render_template('dashboard-admin-global.html')

@app.route('/dashboard-pme')
def dashboard_pme():
    return render_template('dashboard-admin-pme.html')

@app.route('/dashboard-employee')
def dashboard_employee():
    return render_template('dashboard-employee.html')

# ==============================
# AUTHENTIFICATION (LOGIN)
# ==============================
@app.route('/login', methods=['POST'])
def login_post():
    try:
        data = request.json
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"success": False, "message": "Email et mot de passe requis"}), 400

        user = UserService.get_user_by_email_raw(email)
        if not user:
            return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 401

        if not user.actif:
            return jsonify({"success": False, "message": "Compte désactivé. Contactez votre administrateur."}), 403

        if not check_password_hash(user.password, password):
            return jsonify({"success": False, "message": "Mot de passe incorrect"}), 401

        if user.totp_enabled and user.totp_secret:
            from utils.jwt_manager import generer_token_2fa_pending
            temp_token = generer_token_2fa_pending(user.id)
            return jsonify({
                "success": True,
                "requires_2fa": True,
                "temp_token": temp_token,
                "message": "Saisissez le code de votre application d'authentification.",
            }), 200

        token = generer_token(user.id, user.role, user.entreprise_id)

        return jsonify({
            "success": True,
            "token": token,
            "user": {
                "id": user.id,
                "nom": user.nom,
                "role": user.role,
                "entreprise_id": user.entreprise_id
            }
        }), 200

    except Exception as e:
        print(f"[ERREUR] login_post: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/login/verify-2fa', methods=['POST'])
def login_verify_2fa():
    """Valide le code TOTP et délivre le JWT complet."""
    try:
        from utils.jwt_manager import verifier_token_2fa_pending, generer_token
        from utils.totp_helper import verify_totp
        from models_sqlalchemy import User

        data = request.json or {}
        temp_token = data.get('temp_token')
        code = data.get('code', '')

        if not temp_token or not code:
            return jsonify({"success": False, "message": "Code et session requis"}), 400

        user_id = verifier_token_2fa_pending(temp_token)
        if not user_id:
            return jsonify({"success": False, "message": "Session expirée. Reconnectez-vous."}), 401

        user = User.query.get(user_id)
        if not user or not user.actif or not user.totp_enabled or not user.totp_secret:
            return jsonify({"success": False, "message": "Authentification impossible"}), 403

        if not verify_totp(user.totp_secret, code):
            return jsonify({"success": False, "message": "Code incorrect ou expiré"}), 401

        token = generer_token(user.id, user.role, user.entreprise_id)
        return jsonify({
            "success": True,
            "token": token,
            "user": {
                "id": user.id,
                "nom": user.nom,
                "role": user.role,
                "entreprise_id": user.entreprise_id,
            },
        }), 200
    except Exception as e:
        print(f"[ERREUR] login_verify_2fa: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

# ============================================
# ROUTES API ADMIN PME (SANS DOUBLONS)
# ============================================
@app.route("/api/pme/stats", methods=["GET"])
@token_required
@role_required(['admin_pme'])
def pme_stats():
    try:
        entreprise_id = request.user_entreprise_id
        stats = AdminService.get_pme_stats(entreprise_id)
        
        return jsonify({
            "success": True,
            "stats": {
                "total_documents": stats['total_documents'],
                "total_employes": stats['total_employes'],
                "en_attente": stats['en_attente'],
                "valides": stats['valides'],
                "brouillons": stats.get('brouillons', 0),
                "rejetes": stats.get('rejetes', 0),
                "publies": stats.get('publies', 0),
            }
        }), 200
    except Exception as e:
        print(f"[ERREUR] pme_stats: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/pme/documents", methods=["GET"])
@token_required
@role_required(['admin_pme'])
def pme_documents():
    try:
        entreprise_id = request.user_entreprise_id
        search = request.args.get('search')
        statut = request.args.get('statut')
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 15, type=int)
        result = AdminService.get_pme_documents(
            entreprise_id, search=search, statut=statut, page=page, limit=limit
        )
        documents = result['documents']

        for doc in documents:
            if doc.get('date_creation'):
                doc['date_creation'] = str(doc['date_creation'])

        return jsonify({
            "success": True,
            "documents": documents,
            "total": result['total'],
            "total_pages": result['total_pages'],
            "page": result['page'],
        }), 200
    except Exception as e:
        print(f"[ERREUR] pme_documents: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/pme/employes", methods=["GET"])
@token_required
@role_required(['admin_pme'])
def pme_employes():
    try:
        entreprise_id = request.user_entreprise_id
        employes = AdminService.get_pme_employees(entreprise_id)
        
        for emp in employes:
            if emp.get('date_inscription'):
                emp['date_inscription'] = str(emp['date_inscription'])
        
        return jsonify({"success": True, "employes": employes}), 200
    except Exception as e:
        print(f"[ERREUR] pme_employes: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/pme/validation", methods=["GET"])
@token_required
@role_required(['admin_pme'])
def pme_validation():
    try:
        entreprise_id = request.user_entreprise_id
        documents = AdminService.get_pme_validation_documents(entreprise_id)
        
        for doc in documents:
            if doc.get('date_creation'):
                doc['date_creation'] = str(doc['date_creation'])
        
        return jsonify({"success": True, "documents": documents}), 200
    except Exception as e:
        print(f"[ERREUR] pme_validation: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/pme/corbeille", methods=["GET"])
@token_required
@role_required(['admin_pme'])
def pme_corbeille():
    try:
        entreprise_id = request.user_entreprise_id
        documents = AdminService.get_pme_deleted_documents(entreprise_id)
        
        for doc in documents:
            if doc.get('date_suppression'):
                doc['date_suppression'] = str(doc['date_suppression'])
        
        return jsonify({"success": True, "documents": documents}), 200
    except Exception as e:
        print(f"[ERREUR] pme_corbeille: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/pme/documents/export", methods=["GET"])
@token_required
@role_required(['admin_pme'])
def pme_export_documents():
    """Export des documents en CSV (corrigé)"""
    try:
        import csv
        from io import StringIO, BytesIO
        from datetime import datetime
        
        entreprise_id = request.user_entreprise_id
        docs = AdminService.export_pme_documents(entreprise_id)
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Titre', 'Statut', 'Date', 'Auteur'])
        
        for doc in docs:
            writer.writerow([
                doc.get('titre', ''), 
                doc.get('statut', ''), 
                doc.get('date_creation', ''), 
                doc.get('auteur', '')
            ])

        bytes_out = BytesIO(output.getvalue().encode('utf-8'))
        bytes_out.seek(0)
        
        return send_file(
            bytes_out, 
            as_attachment=True, 
            download_name=f"documents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 
            mimetype='text/csv'
        )
    except Exception as e:
        print(f"[ERREUR] pme_export_documents: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/pme/backup", methods=["POST"])
@token_required
@role_required(['admin_pme'])
def pme_backup():
    """Sauvegarde manuelle de la base de données."""
    try:
        import subprocess
        from config import Config

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        backup_file = os.path.join(backup_dir, f"pme_backup_{timestamp}.sql")
        backup_file_abs = os.path.abspath(backup_file)

        mysqldump_paths = [
            r"C:\xampp\mysql\bin\mysqldump.exe",
            r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe",
            "mysqldump",
        ]
        mysqldump_path = next(
            (p for p in mysqldump_paths if p == "mysqldump" or os.path.isfile(p)),
            "mysqldump",
        )

        cmd = [mysqldump_path, "-h", Config.MYSQL_HOST, "-u", Config.MYSQL_USER]
        if Config.MYSQL_PASSWORD:
            cmd.append("-p" + Config.MYSQL_PASSWORD)
        cmd.extend([Config.MYSQL_DB, f"--result-file={backup_file_abs}"])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and os.path.exists(backup_file_abs) and os.path.getsize(backup_file_abs) > 0:
            return jsonify({"success": True, "message": f"Sauvegarde effectuée : {backup_file}"}), 200
        return jsonify({
            "success": False,
            "message": result.stderr or "mysqldump introuvable ou échec de la sauvegarde"
        }), 500
    except Exception as e:
        print(f"[ERREUR] pme_backup: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/pme/document/<int:doc_id>/historique", methods=["GET"])
@token_required
@role_required(['admin_pme'])
def pme_document_historique(doc_id):
    try:
        historique = AdminService.get_document_history(doc_id)
        
        for h in historique:
            if h.get('date_action'):
                h['date_action'] = str(h['date_action'])
        
        return jsonify({"success": True, "historique": historique}), 200
    except Exception as e:
        print(f"[ERREUR] pme_document_historique: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/workflow/config", methods=["GET"])
@token_required
@role_required(['admin_pme'])
def get_workflow_config():
    try:
        config = AdminService.get_workflow_config(request.user_entreprise_id)
        return jsonify({"success": True, "config": config}), 200
    except Exception as e:
        print(f"[ERREUR] get_workflow_config: {e}")
        return jsonify({"success": False, "config": []}), 200

@app.route("/api/workflow/config", methods=["POST"])
@token_required
@role_required(['admin_pme'])
def save_workflow_config():
    try:
        data = request.json
        etapes = data.get('etapes', [])
        AdminService.save_workflow_config(request.user_entreprise_id, etapes)
        return jsonify({"success": True, "message": "Workflow enregistré"}), 200
    except Exception as e:
        print(f"[ERREUR] save_workflow_config: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

# ============================================
# PHOTO ET LOGO
# ============================================
@app.route("/api/user/photo", methods=["GET", "POST"])
@token_required
def user_photo():
    if request.method == "POST":
        file = request.files.get('photo')
        if file:
            filename = f"user_{request.user_id}.jpg"
            upload_dir = os.path.join('static', 'uploads', 'profiles')
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            user = User.query.get(request.user_id)
            if user:
                user.photo_url = f'/static/uploads/profiles/{filename}?t={int(datetime.utcnow().timestamp())}'
                db.session.commit()
            return jsonify({"success": True, "message": "Photo mise à jour", "photo_url": user.photo_url if user else None})
        return jsonify({"success": False, "message": "Aucun fichier"}), 400
    else:
        filepath = os.path.join('static', 'uploads', 'profiles', f"user_{request.user_id}.jpg")
        if os.path.exists(filepath):
            return send_file(filepath, mimetype='image/jpeg')
        return '', 204

@app.route("/api/entreprise/logo", methods=["GET", "POST"])
@token_required
def entreprise_logo():
    user = UserService.get_user_by_id(request.user_id)
    if not user:
        return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 404
    entreprise_id = user.get('entreprise_id')
    
    if request.method == "POST":
        file = request.files.get('logo')
        if file:
            filename = f"entreprise_{entreprise_id}.jpg"
            upload_dir = os.path.join('static', 'uploads', 'logos')
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            return jsonify({"success": True, "message": "Logo mis à jour"})
        return jsonify({"success": False, "message": "Aucun fichier"}), 400
    else:
        filepath = os.path.join('static', 'uploads', 'logos', f"entreprise_{entreprise_id}.jpg")
        if os.path.exists(filepath):
            return send_file(filepath, mimetype='image/jpeg')
        return '', 204

# ============================================
# ROUTES DOCUMENTS (SANS DOUBLONS)
# ============================================

def _can_access_document(doc, user_id, role, entreprise_id):
    if not doc or doc.statut == 'detruit':
        return False
    if role == 'admin_global':
        return True
    if role == 'admin_pme' and doc.entreprise_id == entreprise_id:
        return True
    if role == 'employe':
        return doc.auteur_id == user_id
    if doc.auteur_id == user_id:
        return True
    return False


@app.route('/documents/<int:doc_id>', methods=['GET'])
@token_required
def get_document_by_id(doc_id):
    """Récupérer un document spécifique"""
    try:
        doc = Document.query.filter(
            Document.id == doc_id,
            Document.supprime_le.is_(None)
        ).first()

        if not doc or not _can_access_document(doc, request.user_id, request.user_role, request.user_entreprise_id):
            return jsonify({'error': 'Document non trouvé'}), 404

        return jsonify({'success': True, 'document': doc.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/documents/<int:doc_id>', methods=['PUT'])
@token_required
def update_document_by_id(doc_id):
    """Mettre à jour un document (titre, description, categorie) avec versionnage."""
    try:
        data = request.get_json(silent=True) or {}
        doc = Document.query.filter(
            Document.id == doc_id,
            Document.auteur_id == request.user_id,
            Document.statut.in_(['brouillon', 'rejete']),
            Document.supprime_le.is_(None)
        ).first()

        if not doc:
            return jsonify({'error': 'Document non trouvé ou non modifiable'}), 404

        VersionService.create_snapshot(doc, request.user_id, 'Sauvegarde avant modification')

        if 'titre' in data:
            doc.titre = data['titre']
        if 'description' in data:
            doc.description = data['description']
        if 'categorie_id' in data:
            doc.categorie_id = data['categorie_id']
        doc.version_actuelle = VersionService._next_version_numero(doc.id)
        doc.date_modification = datetime.utcnow()
        db.session.commit()

        IndexationService.index_document(
            doc.id, titre=doc.titre, description=doc.description, contenu_ocr=doc.contenu_ocr
        )

        log = Log(
            action='MODIFICATION',
            description=f"Document {doc_id} modifié (v{doc.version_actuelle})",
            user_id=request.user_id,
            document_id=doc_id,
            date_action=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Document mis à jour', 'document': doc.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/documents/<int:doc_id>', methods=['DELETE'])
@token_required
def delete_document_by_id(doc_id):
    """Supprimer un document (soft delete)"""
    try:
        doc = Document.query.filter(
            Document.id == doc_id,
            Document.auteur_id == request.user_id,
            Document.supprime_le.is_(None)
        ).first()

        if not doc:
            return jsonify({'error': 'Document non trouvé'}), 404

        doc.supprime_le = datetime.utcnow()
        doc.supprime_par = request.user_id
        db.session.commit()

        return jsonify({'success': True, 'message': 'Document supprimé'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/documents/stats', methods=['GET'])
@token_required
def get_documents_stats():
    """Statistiques des documents"""
    try:
        base_query = Document.query.filter(
            Document.auteur_id == request.user_id,
            Document.supprime_le.is_(None)
        )
        stats = {
            'total': base_query.count(),
            'en_attente': base_query.filter(Document.statut == 'soumis').count(),
            'valides': base_query.filter(Document.statut == 'valide').count(),
            'rejetes': base_query.filter(Document.statut == 'rejete').count(),
            'brouillons': base_query.filter(Document.statut == 'brouillon').count(),
            'publies': base_query.filter(Document.statut == 'publie').count(),
            'obsoletes': base_query.filter(Document.statut == 'obsolete').count(),
        }
        return jsonify({'success': True, 'stats': stats}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/documents/pending', methods=['GET'])
@token_required
def get_pending_documents():
    """Documents en attente de validation"""
    try:
        docs = Document.query.filter(
            Document.auteur_id == request.user_id,
            Document.statut == 'soumis',
            Document.supprime_le.is_(None)
        ).order_by(Document.date_creation.desc()).all()

        return jsonify({'success': True, 'documents': [doc.to_dict() for doc in docs]}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/documents/categorie/<int:categorie_id>', methods=['GET'])
@token_required
def get_documents_by_categorie(categorie_id):
    """Récupérer les documents d'une catégorie"""
    try:
        entreprise_id = request.user_entreprise_id
        query = Document.query.filter(
            Document.categorie_id == categorie_id,
            Document.supprime_le.is_(None)
        )
        if request.user_role == 'employe':
            query = query.filter(Document.auteur_id == request.user_id)
        elif entreprise_id is not None:
            query = query.filter(Document.entreprise_id == entreprise_id)

        documents = query.order_by(Document.date_creation.desc()).all()
        return jsonify({'success': True, 'documents': [doc.to_dict() for doc in documents]}), 200
    except Exception as e:
        print(f"[ERREUR] get_documents_by_categorie: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/documents/<int:doc_id>/contenu', methods=['GET'])
@token_required
def get_document_content(doc_id):
    """Récupérer les détails d'un document"""
    try:
        doc = Document.query.filter(
            Document.id == doc_id,
            Document.supprime_le.is_(None)
        ).first()

        if not doc or not _can_access_document(doc, request.user_id, request.user_role, request.user_entreprise_id):
            return jsonify({'error': 'Document non trouvé'}), 404

        return jsonify({'success': True, 'document': doc.to_dict()}), 200
    except Exception as e:
        print(f"[ERREUR] get_document_content: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/documents/<int:doc_id>/categorie', methods=['PUT'])
@token_required
def deplacer_document_categorie(doc_id):
    """Déplacer un document vers une autre catégorie"""
    try:
        data = request.json or {}
        nouvelle_categorie_id = data.get('categorie_id')

        doc = Document.query.filter(
            Document.id == doc_id,
            Document.supprime_le.is_(None)
        ).first()

        if not doc or not _can_access_document(doc, request.user_id, request.user_role, request.user_entreprise_id):
            return jsonify({'error': 'Document non trouvé'}), 404

        if doc.auteur_id != request.user_id and request.user_role == 'employe':
            return jsonify({'error': 'Seul l\'auteur peut déplacer ce document'}), 403

        if nouvelle_categorie_id in (None, '', 0, '0'):
            doc.categorie_id = None
        else:
            doc.categorie_id = int(nouvelle_categorie_id)
        doc.date_modification = datetime.utcnow()
        db.session.commit()

        return jsonify({'success': True, 'message': 'Document déplacé'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"[ERREUR] deplacer_document_categorie: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/documents/<int:doc_id>/ocr', methods=['POST'])
@token_required
def run_ocr(doc_id):
    """Extraction OCR du contenu d'un document"""
    try:
        doc = Document.query.filter(
            Document.id == doc_id,
            Document.supprime_le.is_(None)
        ).first()

        if not doc or not _can_access_document(doc, request.user_id, request.user_role, request.user_entreprise_id):
            return jsonify({'success': False, 'message': 'Document non trouvé'}), 404

        if doc.contenu_ocr:
            return jsonify({'success': True, 'texte': doc.contenu_ocr, 'cached': True}), 200

        texte, erreur = extract_text_from_file(doc.fichier_chemin)
        if erreur:
            status = 503 if 'Tesseract' in erreur or 'manquante' in erreur else 500
            return jsonify({'success': False, 'message': erreur}), status

        doc.contenu_ocr = texte
        doc.date_modification = datetime.utcnow()
        db.session.commit()

        IndexationService.index_document(
            doc.id, titre=doc.titre, description=doc.description, contenu_ocr=texte
        )

        log = Log(
            action='OCR',
            description=f"OCR effectué sur le document {doc_id}",
            user_id=request.user_id,
            document_id=doc_id,
            date_action=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({'success': True, 'texte': texte}), 200
    except Exception as e:
        db.session.rollback()
        print(f"[ERREUR] run_ocr: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/documents/<int:doc_id>/versions', methods=['GET'])
@token_required
def get_document_versions(doc_id):
    """Historique des versions d'un document"""
    try:
        doc = Document.query.filter(
            Document.id == doc_id,
            Document.supprime_le.is_(None)
        ).first()

        if not doc or not _can_access_document(doc, request.user_id, request.user_role, request.user_entreprise_id):
            return jsonify({'success': False, 'message': 'Document non trouvé'}), 404

        versions = VersionDocument.query.filter_by(document_id=doc_id)\
            .order_by(VersionDocument.version_numero.desc()).all()

        if not versions:
            versions = [VersionDocument(
                document_id=doc.id,
                version_numero=1,
                titre=doc.titre,
                description=doc.description,
                fichier_chemin=doc.fichier_chemin,
                fichier_nom=doc.fichier_nom,
                commentaire='Version initiale',
                date_creation=doc.date_creation or datetime.utcnow(),
                createur_id=doc.auteur_id,
            )]
            db.session.add(versions[0])
            db.session.commit()

        return jsonify({
            'success': True,
            'versions': [v.to_dict() for v in versions]
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"[ERREUR] get_document_versions: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/documents/<int:doc_id>/versions/<int:version_id>/restaurer', methods=['PUT'])
@token_required
def restaurer_version(doc_id, version_id):
    """Restaure une version antérieure d'un document."""
    try:
        doc = Document.query.filter(
            Document.id == doc_id,
            Document.supprime_le.is_(None)
        ).first()
        if not doc or doc.auteur_id != request.user_id:
            return jsonify({'success': False, 'message': 'Document non trouvé'}), 404

        success, message = VersionService.restore_version(doc_id, version_id, request.user_id)
        if not success:
            return jsonify({'success': False, 'message': message}), 400

        log = Log(
            action='RESTAURATION_VERSION',
            description=message,
            user_id=request.user_id,
            document_id=doc_id,
            date_action=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        return jsonify({'success': True, 'message': message}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/archivage/automatique', methods=['POST'])
@token_required
@role_required(['admin_global', 'admin_pme'])
def run_archivage_automatique():
    """Déclenche l'archivage automatique des documents obsolètes."""
    try:
        count = ArchivageService.run_auto_archivage(request.user_id)
        return jsonify({'success': True, 'message': f'{count} document(s) archivé(s)'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/documents/historique', methods=['GET'])
@token_required
def get_user_history():
    """Historique des actions de l'utilisateur connecté"""
    try:
        logs = Log.query.filter_by(user_id=request.user_id)\
            .order_by(Log.date_action.desc()).limit(50).all()

        result = []
        for log in logs:
            entry = log.to_dict()
            if log.document_id and not entry.get('document_titre'):
                doc = Document.query.get(log.document_id)
                entry['document_titre'] = doc.titre if doc else 'Inconnu'
            result.append(entry)

        return jsonify({'success': True, 'logs': result}), 200
    except Exception as e:
        print(f"[ERREUR] get_user_history: {e}")
        return jsonify({'success': True, 'logs': []}), 200


@app.route('/api/categories/<int:categorie_id>/partager', methods=['POST'])
@token_required
def partager_categorie(categorie_id):
    """Partager une catégorie avec un utilisateur par email"""
    try:
        data = request.json or {}
        email = (data.get('email') or '').strip()
        if not email:
            return jsonify({'success': False, 'error': 'Email requis'}), 400

        target = User.query.filter_by(email=email).first()
        if not target:
            return jsonify({'success': False, 'error': 'Utilisateur non trouvé'}), 404

        categorie = Categorie.query.get(categorie_id)
        if not categorie:
            return jsonify({'success': False, 'error': 'Catégorie non trouvée'}), 404

        notif = Notification(
            user_id=target.id,
            type_notif='CATEGORIE_PARTAGEE',
            message=f"Catégorie '{categorie.nom}' partagée avec vous",
            lien=f'/dashboard-employee?categorie={categorie_id}',
            lue=False,
            date_creation=datetime.utcnow()
        )
        db.session.add(notif)
        db.session.commit()

        return jsonify({'success': True, 'message': f"Catégorie partagée avec {email}"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/categories/partager', methods=['POST'])
@token_required
def partager_document():
    """Partager un document avec un utilisateur par email"""
    try:
        data = request.json or {}
        email = (data.get('email') or '').strip()
        doc_id = data.get('document_id')

        if not email or not doc_id:
            return jsonify({'success': False, 'error': 'Email et document requis'}), 400

        target = User.query.filter_by(email=email).first()
        if not target:
            return jsonify({'success': False, 'error': 'Utilisateur non trouvé'}), 404

        doc = Document.query.get(doc_id)
        if not doc:
            return jsonify({'success': False, 'error': 'Document non trouvé'}), 404

        notif = Notification(
            user_id=target.id,
            type_notif='DOCUMENT_PARTAGE',
            message=f"Document '{doc.titre}' partagé avec vous",
            lien=f'/documents/{doc_id}/contenu',
            lue=False,
            date_creation=datetime.utcnow()
        )
        db.session.add(notif)
        db.session.commit()

        return jsonify({'success': True, 'message': f"Document partagé avec {email}"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/debug/user/<email>', methods=['GET'])
def debug_user(email):
    """Route de débogage (désactivée en production)."""
    if not app.debug:
        return jsonify({'error': 'Not found'}), 404
    user = UserService.get_user_by_email(email)
    if user:
        safe = {k: v for k, v in user.items() if k != 'password'}
        return jsonify({
            'keys': list(safe.keys()),
            'has_password': 'password' in user,
            'user': safe
        })
    return jsonify({'error': 'User not found'}), 404

# ==============================
# LANCEMENT DU SERVEUR
# ==============================
if __name__ == "__main__":
    print("=" * 50)
    print("GED-PME - Serveur demarre")
    print("URL: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True)