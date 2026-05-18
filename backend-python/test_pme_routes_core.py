import sys
import os
sys.path.append('.')

from flask import Flask
from routes.pme_routes_core import register_pme_routes_core

# Créer une app de test
app = Flask(__name__)
register_pme_routes_core(app)

print('Test des routes PME SQLAlchemy Core...')

with app.test_client() as client:
    # Test GET /api/pme/employes-core (sans token pour voir l'erreur 401)
    print('Test GET /api/pme/employes-core (sans authentification):')
    response = client.get('/api/pme/employes-core')
    print(f'  Status: {response.status_code}')
    if response.status_code == 401:
        print('   Route enregistrée correctement (401 attendu sans token)')
    else:
        print(f'   Réponse inattendue: {response.get_json()}')

print('Test des routes PME terminé !')