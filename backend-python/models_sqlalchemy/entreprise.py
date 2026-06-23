# models_sqlalchemy/entreprise.py
from extensions import db
from datetime import datetime

class Entreprise(db.Model):
    __tablename__ = 'entreprises'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    nif = db.Column(db.String(50))
    rccm = db.Column(db.String(50))
    secteur_activite = db.Column(db.String(100))
    adresse = db.Column(db.Text)
    telephone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    logo_url = db.Column(db.String(255))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    statut = db.Column(db.String(20), default='actif')

    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'nif': self.nif or '',
            'rccm': self.rccm or '',
            'secteur_activite': self.secteur_activite or '',
            'adresse': self.adresse or '',
            'telephone': self.telephone or '',
            'email': self.email or '',
            'logo_url': self.logo_url or '',
            'date_creation': self.date_creation.isoformat() if self.date_creation else None,
            'statut': self.statut
        }