# models_sqlalchemy/log.py
from extensions import db
from datetime import datetime

class Log(db.Model):
    __tablename__ = 'logs'

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    date_action = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'))
    adresse_ip = db.Column(db.String(45))

    user = db.relationship('User', foreign_keys=[user_id])
    document = db.relationship('Document', foreign_keys=[document_id])

    def to_dict(self):
        return {
            'id': self.id,
            'action': self.action,
            'description': self.description or '',
            'date_action': self.date_action.isoformat() if self.date_action else None,
            'user_id': self.user_id,
            'utilisateur_nom': self.user.nom if self.user else None,
            'role': self.user.role if self.user else None,
            'entreprise_nom': self.user.entreprise.nom if self.user and self.user.entreprise else None,
            'document_id': self.document_id,
            'document_titre': self.document.titre if self.document else None,
            'adresse_ip': self.adresse_ip
        }