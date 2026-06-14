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

    # NOUVELLES COLONNES AJOUTEES
    #date_expiration = db.Column(db.Date)
    #sessions_max = db.Column(db.Integer, default=2)
    #centre_cout = db.Column(db.String(50))
    #metadonnees_defaut = db.Column(db.Text)

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
            'password': self.password,
            #'date_expiration': self.date_expiration.isoformat() if self.date_expiration else None,
            #'sessions_max': self.sessions_max,
            #'centre_cout': self.centre_cout or '',
            #'metadonnees_defaut': self.metadonnees_defaut or '',
        }


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