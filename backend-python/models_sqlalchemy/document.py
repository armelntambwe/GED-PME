# models_sqlalchemy/document.py
from extensions import db
from datetime import datetime

class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    fichier_nom = db.Column(db.String(255))
    fichier_chemin = db.Column(db.String(255))
    fichier_taille = db.Column(db.Integer)
    type_mime = db.Column(db.String(100))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    statut = db.Column(db.String(20), default='brouillon')
    auteur_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprises.id'))
    categorie_id = db.Column(db.Integer)  # Sans ForeignKey pour éviter l'erreur
    validateur_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    date_validation = db.Column(db.DateTime)
    commentaire_rejet = db.Column(db.Text)
    niveau_validation_actuel = db.Column(db.Integer, default=1)
    workflow_termine = db.Column(db.Boolean, default=False)
    supprime_le = db.Column(db.DateTime)
    supprime_par = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Relations simplifiées
    auteur = db.relationship('User', foreign_keys=[auteur_id])
    validateur = db.relationship('User', foreign_keys=[validateur_id])
    entreprise = db.relationship('Entreprise', foreign_keys=[entreprise_id])

    def to_dict(self):
        return {
            'id': self.id,
            'titre': self.titre,
            'description': self.description or '',
            'fichier_nom': self.fichier_nom,
            'fichier_taille': self.fichier_taille,
            'type_mime': self.type_mime,
            'date_creation': self.date_creation.isoformat() if self.date_creation else None,
            'statut': self.statut,
            'auteur_id': self.auteur_id,
            'entreprise_id': self.entreprise_id,
            'categorie_id': self.categorie_id,
            'auteur_nom': self.auteur.nom if self.auteur else None,
            'entreprise_nom': self.entreprise.nom if self.entreprise else None,
            'validateur_id': self.validateur_id,
            'date_validation': self.date_validation.isoformat() if self.date_validation else None,
            'commentaire_rejet': self.commentaire_rejet or '',
            'supprime_le': self.supprime_le.isoformat() if self.supprime_le else None,
            'supprime_par': self.supprime_par
        }