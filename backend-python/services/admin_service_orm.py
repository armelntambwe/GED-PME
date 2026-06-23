"""
Service administrateur - ORM SQLAlchemy pur (sans SQL brut)
Gère les opérations administrateur avec ORM SQLAlchemy
"""

from sqlalchemy import or_, func
from extensions import db
from models_sqlalchemy import User, Entreprise, Document, WorkflowConfig, Log, Categorie
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def _apply_document_search(query, search=None, extension=None):
    """Filtre recherche étendue : titre, fichier, OCR, auteur, type MIME."""
    if search:
        like = f'%{search.strip()}%'
        query = query.outerjoin(User, Document.auteur_id == User.id).filter(
            or_(
                Document.titre.ilike(like),
                Document.description.ilike(like),
                Document.contenu_ocr.ilike(like),
                Document.fichier_nom.ilike(like),
                Document.type_mime.ilike(like),
                User.nom.ilike(like),
                User.email.ilike(like),
            )
        ).distinct()
    if extension:
        ext = extension.strip().lstrip('.').lower()
        if ext:
            query = query.filter(
                or_(
                    Document.fichier_nom.ilike(f'%.{ext}'),
                    Document.type_mime.ilike(f'%{ext}%'),
                )
            )
    return query


def _categorie_for_doc(doc):
    if not doc.categorie_id:
        return None
    return Categorie.query.get(doc.categorie_id)


class AdminService:
    """Service pour les opérations administrateur utilisant ORM SQLAlchemy."""
    
    # ==================== STATISTIQUES ====================
    
    @staticmethod
    def get_global_stats() -> dict:
        """Retourne les statistiques globales du système."""
        try:
            stats = {
                'total_entreprises': Entreprise.query.count(),
                'total_users': User.query.count(),
                'active_users': User.query.filter_by(actif=True).count(),
                'inactive_users': User.query.filter_by(actif=False).count(),
                'total_documents': Document.query.filter(
                    Document.supprime_le.is_(None)
                ).count(),
            }
            return stats
        except Exception as e:
            logger.error(f"Erreur get_global_stats: {e}")
            raise
    
    @staticmethod
    def get_company_stats(entreprise_id: int) -> dict:
        """Retourne les statistiques pour une entreprise spécifique."""
        try:
            stats = {
                'total_users': User.query.filter_by(entreprise_id=entreprise_id).count(),
                'active_users': User.query.filter_by(
                    entreprise_id=entreprise_id,
                    actif=True
                ).count(),
                'total_documents': Document.query.filter(
                    Document.entreprise_id == entreprise_id,
                    Document.supprime_le.is_(None)
                ).count(),
                'company': None
            }
            
            company = Entreprise.query.get(entreprise_id)
            if company:
                stats['company'] = company.to_dict()
            
            return stats
        except Exception as e:
            logger.error(f"Erreur get_company_stats: {e}")
            raise
    
    # ==================== GESTION UTILISATEURS ====================
    
    @staticmethod
    def list_all_users(limit: int = 100, offset: int = 0) -> list:
        """Liste tous les utilisateurs avec pagination."""
        try:
            users = User.query.offset(offset).limit(limit).all()
            return [user.to_dict() for user in users]
        except Exception as e:
            logger.error(f"Erreur list_all_users: {e}")
            raise
    
    @staticmethod
    def list_company_users(entreprise_id: int, limit: int = 100, offset: int = 0) -> list:
        """Liste les utilisateurs d'une entreprise."""
        try:
            users = User.query.filter_by(
                entreprise_id=entreprise_id
            ).offset(offset).limit(limit).all()
            return [user.to_dict() for user in users]
        except Exception as e:
            logger.error(f"Erreur list_company_users: {e}")
            raise
    
    @staticmethod
    def toggle_user(user_id: int) -> dict:
        """Active/désactive un utilisateur et retourne le nouvel état."""
        try:
            user = User.query.get(user_id)
            if not user:
                return None
            
            user.actif = not user.actif
            db.session.commit()
            
            return {
                'user_id': user.id,
                'nom': user.nom,
                'actif': user.actif,
                'message': f"Utilisateur {'activé' if user.actif else 'désactivé'}"
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur toggle_user: {e}")
            raise
    
    @staticmethod
    def update_user_role(user_id: int, new_role: str) -> bool:
        """Met à jour le rôle d'un utilisateur."""
        try:
            user = User.query.get(user_id)
            if not user:
                return False
            
            user.role = new_role
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur update_user_role: {e}")
            raise
    
    # ==================== GESTION ENTREPRISES ====================
    
    @staticmethod
    def create_company(nom: str, email: str, telephone: str = '', adresse: str = '') -> int:
        """Crée une nouvelle entreprise. Retourne l'ID de l'entreprise créée."""
        try:
            company = Entreprise(
                nom=nom,
                email=email,
                telephone=telephone or '',
                adresse=adresse or '',
                statut='actif'
            )
            db.session.add(company)
            db.session.commit()
            from services.category_service import CategoryService
            CategoryService.seed_default_categories(company.id)
            return company.id
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur create_company: {e}")
            raise
    
    @staticmethod
    def create_company_with_admin(entreprise_data: dict, administrateur_data: dict) -> dict:
        """Crée une entreprise et un administrateur PME en une seule transaction."""
        try:
            existing_user = User.query.filter_by(email=administrateur_data.get('email')).first()
            if existing_user:
                return {
                    'success': False,
                    'message': 'Cet email est déjà utilisé',
                    'status_code': 409
                }

            company = Entreprise(
                nom=entreprise_data.get('nom'),
                nif=(entreprise_data.get('nif') or '').strip(),
                rccm=(entreprise_data.get('rccm') or '').strip(),
                secteur_activite=(entreprise_data.get('secteur_activite') or '').strip(),
                email=entreprise_data.get('email'),
                telephone=entreprise_data.get('telephone') or '',
                adresse=entreprise_data.get('adresse') or '',
                statut='actif'
            )
            db.session.add(company)
            db.session.flush()

            admin_user = User(
                nom=administrateur_data.get('nom'),
                email=administrateur_data.get('email'),
                password=administrateur_data.get('password'),
                telephone=administrateur_data.get('telephone') or '',
                role='admin_pme',
                entreprise_id=company.id,
                actif=True
            )
            db.session.add(admin_user)
            db.session.flush()

            from services.category_service import CategoryService
            CategoryService.seed_default_categories(company.id, commit=False)

            db.session.commit()

            return {
                'success': True,
                'entreprise_id': company.id,
                'user_id': admin_user.id,
                'status_code': 201
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur create_company_with_admin: {e}")
            raise
    
    @staticmethod
    def list_all_companies(limit: int = 100, offset: int = 0) -> list:
        """Liste toutes les entreprises avec compteurs employés/documents."""
        try:
            companies = Entreprise.query.order_by(Entreprise.nom.asc()).offset(offset).limit(limit).all()
            result = []
            for company in companies:
                data = company.to_dict()
                data['nb_employes'] = User.query.filter_by(
                    entreprise_id=company.id, role='employe'
                ).count()
                data['nb_documents'] = Document.query.filter(
                    Document.entreprise_id == company.id,
                    Document.supprime_le.is_(None),
                ).count()
                result.append(data)
            return result
        except Exception as e:
            logger.error(f"Erreur list_all_companies: {e}")
            raise
    
    @staticmethod
    def get_company(company_id: int) -> dict:
        """Récupère les détails d'une entreprise."""
        try:
            company = Entreprise.query.get(company_id)
            if company:
                company_dict = company.to_dict()
                company_dict['user_count'] = User.query.filter_by(
                    entreprise_id=company_id
                ).count()
                return company_dict
            return None
        except Exception as e:
            logger.error(f"Erreur get_company: {e}")
            raise
    
    @staticmethod
    def toggle_company(company_id: int) -> dict:
        """Active/désactive une entreprise."""
        try:
            company = Entreprise.query.get(company_id)
            if not company:
                return None
            
            new_statut = 'inactif' if company.statut == 'actif' else 'actif'
            company.statut = new_statut
            db.session.commit()
            
            return {
                'company_id': company.id,
                'nom': company.nom,
                'statut': new_statut,
                'message': f"Entreprise {new_statut}"
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur toggle_company: {e}")
            raise
    
    # ==================== RAPPORTS & EXPORT ====================
    
    @staticmethod
    def get_user_activity_report(limit: int = 100, entreprise_id: int = None) -> list:
        """Rapport d'activité enrichi (logs, connexions, uploads)."""
        try:
            query = User.query
            if entreprise_id:
                query = query.filter_by(entreprise_id=entreprise_id)
            users = query.order_by(User.id.desc()).limit(limit).all()
            report = []

            for user in users:
                nb_actions = Log.query.filter_by(user_id=user.id).count()
                nb_docs = Document.query.filter(
                    Document.auteur_id == user.id,
                    Document.supprime_le.is_(None),
                ).count()
                last_log = (
                    Log.query.filter_by(user_id=user.id)
                    .order_by(Log.date_action.desc())
                    .first()
                )
                last_login = (
                    Log.query.filter_by(user_id=user.id, action='CONNEXION')
                    .order_by(Log.date_action.desc())
                    .first()
                )
                ent = user.entreprise
                report.append({
                    'id': user.id,
                    'nom': user.nom,
                    'email': user.email,
                    'role': user.role,
                    'actif': user.actif,
                    'entreprise_id': user.entreprise_id,
                    'entreprise_nom': ent.nom if ent else None,
                    'date_inscription': user.date_inscription.isoformat() if user.date_inscription else None,
                    'nb_actions': nb_actions,
                    'nb_documents': nb_docs,
                    'derniere_action': last_log.date_action.isoformat() if last_log and last_log.date_action else None,
                    'derniere_connexion': last_login.date_action.isoformat() if last_login and last_login.date_action else None,
                })

            return report
        except Exception as e:
            logger.error(f"Erreur get_user_activity_report: {e}")
            raise

    @staticmethod
    def list_global_documents(
        search: str = None,
        statut: str = None,
        entreprise_id: int = None,
        extension: str = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        """Liste paginée des documents sur toute la plateforme."""
        try:
            query = Document.query.filter(Document.supprime_le.is_(None))
            if statut:
                query = query.filter(Document.statut == statut)
            if entreprise_id:
                query = query.filter(Document.entreprise_id == entreprise_id)
            query = _apply_document_search(query, search, extension)

            total = query.count()
            page = max(1, page)
            limit = max(1, min(limit, 200))
            docs = (
                query.order_by(Document.date_creation.desc())
                .offset((page - 1) * limit)
                .limit(limit)
                .all()
            )

            result = []
            for doc in docs:
                d = doc.to_dict()
                result.append(d)

            return {
                'documents': result,
                'total': total,
                'total_pages': max(1, (total + limit - 1) // limit),
                'page': page,
            }
        except Exception as e:
            logger.error(f"Erreur list_global_documents: {e}")
            raise

    @staticmethod
    def list_pending_validation_documents(limit: int = 100) -> list:
        """Documents en attente de validation (toutes entreprises)."""
        try:
            docs = (
                Document.query.filter(
                    Document.statut == 'soumis',
                    Document.supprime_le.is_(None),
                )
                .order_by(Document.date_creation.desc())
                .limit(limit)
                .all()
            )
            return [d.to_dict() for d in docs]
        except Exception as e:
            logger.error(f"Erreur list_pending_validation_documents: {e}")
            raise

    @staticmethod
    def get_company_detail(entreprise_id: int) -> dict:
        """Fiche entreprise complète avec stats et listes récentes."""
        try:
            company = Entreprise.query.get(entreprise_id)
            if not company:
                return None
            data = company.to_dict()
            data['stats'] = AdminService.get_pme_stats(entreprise_id)
            data['nb_admins'] = User.query.filter_by(
                entreprise_id=entreprise_id, role='admin_pme'
            ).count()
            data['employes'] = [
                u.to_dict() for u in User.query.filter_by(entreprise_id=entreprise_id)
                .order_by(User.id.desc()).limit(50).all()
            ]
            recent = (
                Document.query.filter(
                    Document.entreprise_id == entreprise_id,
                    Document.supprime_le.is_(None),
                )
                .order_by(Document.date_creation.desc())
                .limit(10)
                .all()
            )
            data['documents_recents'] = [d.to_dict() for d in recent]
            data['categories'] = AdminService.get_category_document_counts(entreprise_id)
            return data
        except Exception as e:
            logger.error(f"Erreur get_company_detail: {e}")
            raise

    @staticmethod
    def update_company_fields(company_id: int, data: dict) -> bool:
        """Met à jour tous les champs entreprise."""
        try:
            company = Entreprise.query.get(company_id)
            if not company:
                return False
            for field in ('nom', 'nif', 'rccm', 'secteur_activite', 'adresse', 'telephone', 'email', 'statut'):
                if field in data:
                    setattr(company, field, data[field])
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur update_company_fields: {e}")
            raise

    @staticmethod
    def hard_delete_company(company_id: int) -> dict:
        """Suppression définitive entreprise (documents, users, catégories)."""
        try:
            company = Entreprise.query.get(company_id)
            if not company:
                return {'success': False, 'message': 'Entreprise non trouvée'}

            Document.query.filter_by(entreprise_id=company_id).delete()
            Categorie.query.filter_by(entreprise_id=company_id).delete()
            WorkflowConfig.query.filter_by(entreprise_id=company_id).delete()
            User.query.filter_by(entreprise_id=company_id).delete()
            db.session.delete(company)
            db.session.commit()
            return {'success': True, 'message': 'Entreprise supprimée définitivement'}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur hard_delete_company: {e}")
            raise

    @staticmethod
    def list_users_filtered(
        role: str = None,
        entreprise_id: int = None,
        actif: str = None,
        search: str = None,
        page: int = 1,
        limit: int = 50,
    ) -> dict:
        """Liste utilisateurs avec filtres et pagination."""
        try:
            query = User.query
            if role:
                query = query.filter(User.role == role)
            if entreprise_id:
                query = query.filter(User.entreprise_id == entreprise_id)
            if actif is not None and actif != '':
                query = query.filter(User.actif == (str(actif).lower() in ('1', 'true', 'oui', 'actif')))
            if search:
                like = f'%{search}%'
                query = query.filter(or_(User.nom.ilike(like), User.email.ilike(like)))

            total = query.count()
            page = max(1, page)
            limit = max(1, min(limit, 500))
            users = query.order_by(User.id.desc()).offset((page - 1) * limit).limit(limit).all()
            result = []
            for user in users:
                d = user.to_dict()
                d['entreprise_nom'] = user.entreprise.nom if user.entreprise else None
                result.append(d)
            return {
                'users': result,
                'total': total,
                'total_pages': max(1, (total + limit - 1) // limit),
                'page': page,
            }
        except Exception as e:
            logger.error(f"Erreur list_users_filtered: {e}")
            raise

    @staticmethod
    def delete_user(user_id: int, current_user_id: int) -> dict:
        """Supprime un utilisateur (protections intégrées)."""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'message': 'Utilisateur non trouvé', 'status': 404}
            if user.id == current_user_id:
                return {'success': False, 'message': 'Vous ne pouvez pas supprimer votre propre compte', 'status': 400}
            if user.role == 'admin_global':
                others = User.query.filter(
                    User.role == 'admin_global',
                    User.id != user_id,
                    User.actif.is_(True),
                ).count()
                if others == 0:
                    return {'success': False, 'message': 'Impossible de supprimer le dernier admin global actif', 'status': 400}
            db.session.delete(user)
            db.session.commit()
            return {'success': True, 'message': 'Utilisateur supprimé'}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur delete_user: {e}")
            raise

    @staticmethod
    def get_platform_settings_view() -> dict:
        """Vue lecture seule des paramètres plateforme (secrets masqués)."""
        from config import (
            WHATSAPP_ENABLED, WHATSAPP_PROVIDER, MAIL_ENABLED, MAIL_SERVER, MAIL_PORT,
            MAIL_FROM, DEFAULT_PHONE_PREFIX, APP_BASE_URL, UPLOAD_FOLDER, MAX_CONTENT_LENGTH,
        )
        from utils.platform_settings import load_platform_settings
        from utils.whatsapp_helper import is_whatsapp_configured

        ps = load_platform_settings()
        return {
            'maintenance_mode': ps.get('maintenance_mode', False),
            'maintenance_message': ps.get('maintenance_message', ''),
            'whatsapp_enabled': WHATSAPP_ENABLED,
            'whatsapp_provider': WHATSAPP_PROVIDER,
            'whatsapp_configured': is_whatsapp_configured(),
            'mail_enabled': MAIL_ENABLED,
            'mail_server': MAIL_SERVER,
            'mail_port': MAIL_PORT,
            'mail_from': MAIL_FROM,
            'phone_prefix': DEFAULT_PHONE_PREFIX,
            'app_base_url': APP_BASE_URL,
            'upload_folder': UPLOAD_FOLDER,
            'max_upload_mb': MAX_CONTENT_LENGTH // (1024 * 1024),
            'version': 'GED-PME 2.0',
        }

    @staticmethod
    def get_platform_health() -> dict:
        """Santé système (DB, disque, OCR)."""
        import os
        from utils.db import test_connection
        from config import UPLOAD_FOLDER

        db_ok, db_msg = test_connection()
        upload_size = 0
        file_count = 0
        if os.path.exists(UPLOAD_FOLDER):
            for dirpath, _, files in os.walk(UPLOAD_FOLDER):
                file_count += len(files)
                for f in files:
                    fp = os.path.join(dirpath, f)
                    if os.path.isfile(fp):
                        upload_size += os.path.getsize(fp)

        ocr_count = Document.query.filter(
            Document.contenu_ocr.isnot(None),
            Document.contenu_ocr != '',
        ).count()

        return {
            'database_ok': db_ok,
            'database_message': db_msg,
            'upload_files': file_count,
            'upload_size_mb': round(upload_size / (1024 * 1024), 2),
            'documents_ocr': ocr_count,
            'total_documents': Document.query.filter(Document.supprime_le.is_(None)).count(),
        }

    @staticmethod
    def list_backups() -> list:
        """Liste les fichiers de sauvegarde SQL."""
        import os
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')
        if not os.path.isdir(backup_dir):
            return []
        files = []
        for name in sorted(os.listdir(backup_dir), reverse=True):
            if not name.endswith('.sql'):
                continue
            path = os.path.join(backup_dir, name)
            if os.path.isfile(path):
                files.append({
                    'filename': name,
                    'size_mb': round(os.path.getsize(path) / (1024 * 1024), 2),
                    'date': datetime.fromtimestamp(os.path.getmtime(path)).isoformat(),
                })
        return files
    
    # ==================== PME OPERATIONS ====================
    
    @staticmethod
    def get_pme_stats(entreprise_id: int) -> dict:
        """Retourne les statistiques PME pour une entreprise."""
        try:
            base = Document.query.filter(
                Document.entreprise_id == entreprise_id,
                Document.supprime_le.is_(None)
            )
            stats = {
                'total_documents': base.count(),
                'total_employes': User.query.filter_by(
                    entreprise_id=entreprise_id,
                    role='employe'
                ).count(),
                'en_attente': base.filter(Document.statut == 'soumis').count(),
                'valides': base.filter(Document.statut == 'valide').count(),
                'brouillons': base.filter(Document.statut == 'brouillon').count(),
                'rejetes': base.filter(Document.statut == 'rejete').count(),
                'publies': base.filter(Document.statut == 'publie').count(),
                'obsoletes': base.filter(Document.statut == 'obsolete').count(),
                'detruits': base.filter(Document.statut == 'detruit').count(),
            }
            return stats
        except Exception as e:
            logger.error(f"Erreur get_pme_stats: {e}")
            raise

    @staticmethod
    def get_category_document_counts(entreprise_id: int) -> list:
        """Nombre de documents par catégorie pour une entreprise."""
        try:
            rows = (
                db.session.query(Categorie.nom, func.count(Document.id))
                .outerjoin(
                    Document,
                    (Document.categorie_id == Categorie.id)
                    & (Document.supprime_le.is_(None))
                    & (Document.entreprise_id == entreprise_id),
                )
                .filter(Categorie.entreprise_id == entreprise_id)
                .group_by(Categorie.id, Categorie.nom)
                .order_by(func.count(Document.id).desc())
                .all()
            )
            return [{'nom': nom, 'count': count} for nom, count in rows]
        except Exception as e:
            logger.error(f"Erreur get_category_document_counts: {e}")
            raise
    
    @staticmethod
    def get_pme_documents(entreprise_id: int, search: str = None, statut: str = None,
                          extension: str = None, page: int = 1, limit: int = 15) -> dict:
        """Retourne la liste paginée des documents PME avec auteurs et catégories."""
        try:
            if entreprise_id is None:
                return {'documents': [], 'total': 0, 'total_pages': 1, 'page': page}

            query = Document.query.filter(
                Document.entreprise_id == entreprise_id,
                Document.supprime_le.is_(None),
                Document.statut != 'detruit',
            )
            if statut:
                query = query.filter(Document.statut == statut)
            query = _apply_document_search(query, search, extension)

            total = query.count()
            page = max(1, page)
            limit = max(1, min(limit, 200))
            documents = (
                query.order_by(Document.date_creation.desc())
                .offset((page - 1) * limit)
                .limit(limit)
                .all()
            )

            result = []
            for doc in documents:
                auteur = User.query.get(doc.auteur_id)
                categorie = _categorie_for_doc(doc)
                doc_dict = doc.to_dict()
                doc_dict['auteur_nom'] = auteur.nom if auteur else None
                doc_dict['categorie_nom'] = categorie.nom if categorie else None
                result.append(doc_dict)

            total_pages = max(1, (total + limit - 1) // limit)
            return {
                'documents': result,
                'total': total,
                'total_pages': total_pages,
                'page': page,
            }
        except Exception as e:
            logger.error(f"Erreur get_pme_documents: {e}")
            raise
    
    @staticmethod
    def get_pme_employees(entreprise_id: int) -> list:
        """Retourne la liste des employés PME."""
        try:
            employees = User.query.filter_by(
                entreprise_id=entreprise_id,
                role='employe'
            ).order_by(User.id.desc()).all()
            
            return [emp.to_dict() for emp in employees]
        except Exception as e:
            logger.error(f"Erreur get_pme_employees: {e}")
            raise
    
    @staticmethod
    def get_pme_validation_documents(entreprise_id: int) -> list:
        """Retourne les documents en attente de validation."""
        try:
            documents = Document.query.filter(
                Document.entreprise_id == entreprise_id,
                Document.statut == 'soumis',
                Document.supprime_le.is_(None)
            ).order_by(Document.date_creation.desc()).all()
            
            result = []
            for doc in documents:
                auteur = User.query.get(doc.auteur_id)
                categorie = _categorie_for_doc(doc)
                doc_dict = doc.to_dict()
                doc_dict['auteur_nom'] = auteur.nom if auteur else None
                doc_dict['categorie_nom'] = categorie.nom if categorie else None
                result.append(doc_dict)
            
            return result
        except Exception as e:
            logger.error(f"Erreur get_pme_validation_documents: {e}")
            raise
    
    @staticmethod
    def get_pme_deleted_documents(entreprise_id: int) -> list:
        """Retourne les documents supprimés (corbeille)."""
        try:
            documents = Document.query.filter(
                Document.entreprise_id == entreprise_id,
                Document.supprime_le.isnot(None)
            ).order_by(Document.supprime_le.desc()).all()
            
            result = []
            for doc in documents:
                result.append({
                    'id': doc.id,
                    'titre': doc.titre,
                    'date_suppression': doc.supprime_le.isoformat() if doc.supprime_le else None
                })
            
            return result
        except Exception as e:
            logger.error(f"Erreur get_pme_deleted_documents: {e}")
            raise
    
    @staticmethod
    def export_pme_documents(entreprise_id: int) -> list:
        """Exporte les documents PME pour CSV."""
        try:
            documents = Document.query.filter_by(entreprise_id=entreprise_id)\
                .filter(Document.supprime_le.is_(None))\
                .order_by(Document.date_creation.desc())\
                .all()
            
            result = []
            for doc in documents:
                auteur = User.query.get(doc.auteur_id)
                result.append({
                    'titre': doc.titre,
                    'statut': doc.statut,
                    'date_creation': doc.date_creation.isoformat() if doc.date_creation else None,
                    'auteur': auteur.nom if auteur else None
                })
            
            return result
        except Exception as e:
            logger.error(f"Erreur export_pme_documents: {e}")
            raise
    
    @staticmethod
    def get_document_history(document_id: int) -> list:
        """Retourne l'historique d'un document."""
        try:
            logs = Log.query.filter_by(document_id=document_id)\
                .order_by(Log.date_action.desc())\
                .all()
            
            result = []
            for log in logs:
                user = User.query.get(log.user_id)
                result.append({
                    'action': log.action,
                    'description': log.description,
                    'date_action': log.date_action.isoformat() if log.date_action else None,
                    'utilisateur_nom': user.nom if user else None
                })
            
            return result
        except Exception as e:
            logger.error(f"Erreur get_document_history: {e}")
            raise
    
    @staticmethod
    def get_workflow_config(entreprise_id: int) -> list:
        """Retourne la configuration workflow d'une entreprise."""
        try:
            configs = WorkflowConfig.query.filter_by(entreprise_id=entreprise_id)\
                .order_by(WorkflowConfig.ordre)\
                .all()
            
            return [config.to_dict() for config in configs]
        except Exception as e:
            logger.error(f"Erreur get_workflow_config: {e}")
            raise
    
    @staticmethod
    def save_workflow_config(entreprise_id: int, etapes: list) -> bool:
        """Sauvegarde la configuration workflow."""
        try:
            # Supprimer l'ancienne configuration
            WorkflowConfig.query.filter_by(entreprise_id=entreprise_id).delete()
            
            # Ajouter la nouvelle configuration
            for i, etape in enumerate(etapes):
                config = WorkflowConfig(
                    entreprise_id=entreprise_id,
                    nom_etape=etape['nom'],
                    role_requis=etape['role'],
                    ordre=i + 1,
                    delai_heures=etape.get('delai', 48)
                )
                db.session.add(config)
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erreur save_workflow_config: {e}")
            raise