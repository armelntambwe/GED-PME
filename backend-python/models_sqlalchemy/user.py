# models_sqlalchemy/user.py
from extensions import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    telephone = db.Column(db.String(20))
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='employe')
    actif = db.Column(db.Boolean, default=True)
    date_inscription = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprises.id'))

    # Relations
    entreprise = db.relationship('Entreprise', backref='users')

    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'email': self.email,
            'telephone': self.telephone or '',
            'role': self.role,
            'actif': self.actif,
            'entreprise_id': self.entreprise_id,
            'date_inscription': self.date_inscription.isoformat() if self.date_inscription else None,
            'password': self.password 
        }

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()