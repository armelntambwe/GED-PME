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
    poste = db.Column(db.String(100))
    service = db.Column(db.String(100))
    photo_url = db.Column(db.String(255))
    notify_whatsapp = db.Column(db.Boolean, default=False)
    whatsapp_api_key = db.Column(db.String(64))
    totp_secret = db.Column(db.String(64))
    totp_enabled = db.Column(db.Boolean, default=False)

    entreprise = db.relationship('Entreprise', backref='users')

    def to_dict(self, include_password=False):
        data = {
            'id': self.id,
            'nom': self.nom,
            'email': self.email,
            'telephone': self.telephone or '',
            'role': self.role,
            'actif': self.actif,
            'entreprise_id': self.entreprise_id,
            'poste': self.poste or '',
            'service': self.service or '',
            'photo_url': self.photo_url or '',
            'notify_whatsapp': bool(self.notify_whatsapp),
            'whatsapp_api_key_set': bool(self.whatsapp_api_key),
            'totp_enabled': bool(self.totp_enabled),
            'date_inscription': self.date_inscription.isoformat() if self.date_inscription else None,
        }
        if include_password:
            data['password'] = self.password
        return data


class DroitsUtilisateur(db.Model):
    __tablename__ = 'droits_utilisateur'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    droit_lecture = db.Column(db.Boolean, default=True)
    droit_creation = db.Column(db.Boolean, default=False)
    droit_modification = db.Column(db.Boolean, default=False)
    droit_suppression = db.Column(db.Boolean, default=False)
    droit_export = db.Column(db.Boolean, default=False)
    droit_admin = db.Column(db.Boolean, default=False)

    # Relation
    user = db.relationship('User', backref='droits')

    def to_dict(self):
        return {
            'lecture': self.droit_lecture,
            'creation': self.droit_creation,
            'modification': self.droit_modification,
            'suppression': self.droit_suppression,
            'export': self.droit_export,
            'admin': self.droit_admin
        }