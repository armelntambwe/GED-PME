from extensions import db

class WorkflowConfig(db.Model):
    __tablename__ = 'workflow_config'

    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprises.id'), nullable=False)
    nom_etape = db.Column(db.String(150), nullable=False)
    role_requis = db.Column(db.String(50), nullable=False)
    ordre = db.Column(db.Integer, nullable=False)
    delai_heures = db.Column(db.Integer, nullable=False, default=48)

    def to_dict(self):
        return {
            'id': self.id,
            'entreprise_id': self.entreprise_id,
            'nom_etape': self.nom_etape,
            'role_requis': self.role_requis,
            'ordre': self.ordre,
            'delai_heures': self.delai_heures
        }
