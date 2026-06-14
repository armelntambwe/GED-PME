# app.py - Version temporaire qui fonctionne
from flask import Flask, send_from_directory, render_template, request, jsonify, send_file
from config import Config
from utils.db import get_db, test_connection
from middleware.auth import token_required, role_required
from werkzeug.security import generate_password_hash, check_password_hash
from utils.jwt_manager import generer_token
from extensions import db, migrate

# Importer les modèles SQLAlchemy
from models_sqlalchemy import Entreprise, User, Document, Categorie, Log

# Routes imports (utiliser celles qui existent)
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

app = Flask(__name__)
app.config.from_object(Config)

# Initialisation SQLAlchemy / Flask-Migrate
db.init_app(app)
migrate.init_app(app, db)

# Test de connexion MySQL
print("Verification MySQL...")
success, message = test_connection()
print(f"{message}" if success else f"{message}")

# Enregistrement des routes (uniquement celles qui existent)
register_authentification_routes(app)
register_document_routes(app)
register_admin_routes_orm(app)
register_user_routes(app)
register_category_routes(app)
register_notification_routes(app)
register_company_routes(app)

# ==============================
# FICHIERS STATIQUES
# ==============================

@app.route('/sw.js')
def serve_sw():
    return send_from_directory('static', 'sw.js')

@app.route('/offline.html')
def serve_offline():
    return send_from_directory('static', 'offline.html')

@app.route('/offline-queue.js')
def serve_offline_queue():
    return send_from_directory('static', 'offline-queue.js')

# ==============================
# INTERFACES UTILISATEUR
# ==============================

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    try:
        data = request.json
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"success": False, "message": "Email et mot de passe requis"}), 400

        user = UserService.get_user_by_email(email)
        if not user:
            return jsonify({"success": False, "message": "Utilisateur non trouvé"}), 401

        if not check_password_hash(user['password'], password):
            return jsonify({"success": False, "message": "Mot de passe incorrect"}), 401

        token = generer_token(user['id'], user['role'], user.get('entreprise_id'))

        return jsonify({
            "success": True,
            "token": token,
            "user": {
                "id": user['id'],
                "nom": user['nom'],
                "role": user['role'],
                "entreprise_id": user.get('entreprise_id')
            }
        }), 200

    except Exception as e:
        print(f"[ERREUR] login_post: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

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

# ============================================
# ROUTES API ADMIN PME (avec services ORM)
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
                "valides": stats['valides']
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
        documents = AdminService.get_pme_documents(entreprise_id)
        
        for doc in documents:
            if doc.get('date_creation'):
                doc['date_creation'] = str(doc['date_creation'])
        
        return jsonify({"success": True, "documents": documents}), 200
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
            writer.writerow([doc.get('titre', ''), doc.get('statut', ''), doc.get('date_creation', ''), doc.get('auteur', '')])

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
# ROUTES PHOTO ET LOGO
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
            return jsonify({"success": True, "message": "Photo mise à jour"})
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

@app.route('/debug/user/<email>', methods=['GET'])
def debug_user(email):
    user = UserService.get_user_by_email(email)
    if user:
        return jsonify({
            'keys': list(user.keys()),
            'has_password': 'password' in user,
            'user': user
        })
    return jsonify({'error': 'User not found'}), 404






@app.route('/documents/<int:doc_id>', methods=['GET'])
@token_required
def get_document_by_id(current_user, doc_id):
    """Récupérer un document spécifique (pour visualisation)"""
    from models_sqlalchemy.document import Document
    
    try:
        doc = Document.query.filter(
            Document.id == doc_id,
            Document.auteur_id == current_user['id'],
            Document.supprime_le.is_(None)
        ).first()
        
        if not doc:
            return jsonify({'error': 'Document non trouvé'}), 404
        
        return jsonify({
            'success': True, 
            'document': doc.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/documents/<int:doc_id>', methods=['PUT'])
@token_required
def update_document_by_id(current_user, doc_id):
    """Mettre à jour un document (titre, description, categorie)"""
    from models_sqlalchemy.document import Document
    from extensions import db
    
    try:
        data = request.get_json()
        
        doc = Document.query.filter(
            Document.id == doc_id,
            Document.auteur_id == current_user['id'],
            Document.statut == 'brouillon',
            Document.supprime_le.is_(None)
        ).first()
        
        if not doc:
            return jsonify({'error': 'Document non trouvé ou non modifiable (seuls les brouillons sont modifiables)'}), 404
        
        if 'titre' in data:
            doc.titre = data['titre']
        if 'description' in data:
            doc.description = data['description']
        if 'categorie_id' in data:
            doc.categorie_id = data['categorie_id']
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Document mis à jour',
            'document': doc.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/documents/<int:doc_id>', methods=['DELETE'])
@token_required
def delete_document_by_id(current_user, doc_id):
    """Supprimer un document (soft delete) - version directe"""
    from models_sqlalchemy.document import Document
    from extensions import db
    from datetime import datetime
    
    try:
        doc = Document.query.filter(
            Document.id == doc_id,
            Document.auteur_id == current_user['id'],
            Document.supprime_le.is_(None)
        ).first()
        
        if not doc:
            return jsonify({'error': 'Document non trouvé'}), 404
        
        doc.supprime_le = datetime.utcnow()
        doc.supprime_par = current_user['id']
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Document supprimé'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/documents/stats', methods=['GET'])
@token_required
def get_documents_stats(current_user):
    """Statistiques des documents (alias vers /api/pme/stats)"""
    from models_sqlalchemy.document import Document
    
    try:
        base_query = Document.query.filter(
            Document.auteur_id == current_user['id'],
            Document.supprime_le.is_(None)
        )
        
        stats = {
            'total': base_query.count(),
            'en_attente': base_query.filter(Document.statut == 'soumis').count(),
            'valides': base_query.filter(Document.statut == 'valide').count(),
            'rejetes': base_query.filter(Document.statut == 'rejete').count(),
            'brouillons': base_query.filter(Document.statut == 'brouillon').count()
        }
        
        return jsonify({'success': True, 'stats': stats}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/documents/pending', methods=['GET'])
@token_required
def get_pending_documents(current_user):
    """Documents en attente de validation (pour onglet Tâches)"""
    from models_sqlalchemy.document import Document
    
    try:
        docs = Document.query.filter(
            Document.auteur_id == current_user['id'],
            Document.statut == 'soumis',
            Document.supprime_le.is_(None)
        ).order_by(Document.date_creation.desc()).all()
        
        return jsonify({
            'success': True,
            'documents': [doc.to_dict() for doc in docs]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500







# ==============================
# LANCEMENT DU SERVEUR
# ==============================

if __name__ == "__main__":
    print("=" * 50)
    print("GED-PME - Serveur demarre")
    print("URL: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True)