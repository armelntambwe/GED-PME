"""
Service administrateur - ORM SQLAlchemy pur (sans SQL brut)
Gère les opérations administrateur avec ORM SQLAlchemy
"""

from sqlalchemy import or_
from extensions import db
from models_sqlalchemy import User, Entreprise, Document, WorkflowConfig, Log, Categorie
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


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
        """Liste toutes les entreprises."""
        try:
            companies = Entreprise.query.offset(offset).limit(limit).all()
            return [company.to_dict() for company in companies]
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
    def get_user_activity_report(limit: int = 100) -> list:
        """Génère un rapport d'activité des utilisateurs."""
        try:
            users = User.query.limit(limit).all()
            report = []
            
            for user in users:
                report.append({
                    'id': user.id,
                    'nom': user.nom,
                    'email': user.email,
                    'role': user.role,
                    'actif': user.actif,
                    'entreprise_id': user.entreprise_id,
                    'date_inscription': user.date_inscription.isoformat() if user.date_inscription else None
                })
            
            return report
        except Exception as e:
            logger.error(f"Erreur get_user_activity_report: {e}")
            raise
    
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
    def get_pme_documents(entreprise_id: int, search: str = None, statut: str = None,
                          page: int = 1, limit: int = 15) -> dict:
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
            if search:
                like = f'%{search}%'
                query = query.filter(
                    or_(
                        Document.titre.ilike(like),
                        Document.description.ilike(like),
                        Document.contenu_ocr.ilike(like),
                    )
                )

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