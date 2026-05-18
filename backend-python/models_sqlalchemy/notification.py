# models_sqlalchemy/notification.py
from extensions import db
from datetime import datetime

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    type_notif = db.Column('type', db.String(50), nullable=False)
    message = db.Column(db.Text)
    lien = db.Column(db.String(255))
    lue = db.Column(db.Boolean, default=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type_notif,
            'message': self.message or '',
            'lien': self.lien or '',
            'lue': self.lue,
            'date_creation': self.date_creation.isoformat() if self.date_creation else None
        }
