from extensions import db
from datetime import datetime


class ArchiveDocument(db.Model):
    __tablename__ = 'archives'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    date_archivage = db.Column(db.DateTime, default=datetime.utcnow)
    duree_conservation = db.Column(db.Integer, default=365)
    motif = db.Column(db.String(255))
    archive_par = db.Column(db.Integer, db.ForeignKey('users.id'))

    document = db.relationship('Document', foreign_keys=[document_id])

    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'date_archivage': self.date_archivage.isoformat() if self.date_archivage else None,
            'duree_conservation': self.duree_conservation,
            'motif': self.motif,
            'archive_par': self.archive_par,
        }
