from extensions import db
from datetime import datetime


class Categorie(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprises.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    entreprise = db.relationship('Entreprise', foreign_keys=[entreprise_id])

    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'description': self.description or '',
            'entreprise_id': self.entreprise_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
