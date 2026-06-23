# models_sqlalchemy/version.py
from extensions import db
from datetime import datetime

class VersionDocument(db.Model):
    __tablename__ = 'versions_documents'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    version_numero = db.Column(db.Integer, nullable=False)
    titre = db.Column(db.String(200))
    description = db.Column(db.Text)
    fichier_chemin = db.Column(db.String(255))
    fichier_nom = db.Column(db.String(255))
    commentaire = db.Column(db.String(500))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    createur_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    document = db.relationship('Document', foreign_keys=[document_id])
    createur = db.relationship('User', foreign_keys=[createur_id])

    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'version_numero': self.version_numero,
            'titre': self.titre,
            'description': self.description,
            'commentaire': self.commentaire,
            'date_creation': self.date_creation.isoformat() if self.date_creation else None,
            'createur_nom': self.createur.nom if self.createur else None
        }