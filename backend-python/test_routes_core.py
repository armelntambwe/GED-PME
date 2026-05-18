import sys
import os
sys.path.append('.')

from flask import Flask
from routes.category_routes_core import register_category_routes_core

# Créer une app de test
app = Flask(__name__)
register_category_routes_core(app)

print('Test des routes SQLAlchemy Core...')

with app.test_client() as client:
    # Test GET /categories-core (sans token pour voir l'erreur 401)
    print('Test GET /categories-core (sans authentification):')
    response = client.get('/categories-core')
    print(f'  Status: {response.status_code}')
    if response.status_code == 401:
        print('   Route enregistrée correctement (401 attendu sans token)')
    else:
        print(f'   Réponse inattendue: {response.get_json()}')

    # Test POST /categories-core (sans token)
    print('Test POST /categories-core (sans authentification):')
    response = client.post('/categories-core', json={'nom': 'Test Category', 'description': 'Test'})
    print(f'  Status: {response.status_code}')
    if response.status_code == 401:
        print('  ✅ Route POST enregistrée correctement (401 attendu sans token)')
    else:
        print(f'  ❌ Réponse inattendue: {response.get_json()}')

print('Test des routes terminé !')