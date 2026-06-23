from extensions import db
from datetime import datetime


class Indexation(db.Model):
    __tablename__ = 'indexations'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    mot_cle = db.Column(db.String(100), nullable=False)
    date_indexation = db.Column(db.DateTime, default=datetime.utcnow)

    document = db.relationship('Document', foreign_keys=[document_id])

    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'mot_cle': self.mot_cle,
            'date_indexation': self.date_indexation.isoformat() if self.date_indexation else None,
        }
