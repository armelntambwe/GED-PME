# test_orm.py
from app import app
from models_sqlalchemy import User, Entreprise, Document

with app.app_context():
    print("=== Test SQLAlchemy ===\n")
    
    # Compter les utilisateurs
    user_count = User.query.count()
    print(f"Nombre d'utilisateurs: {user_count}")
    
    # Lister les 5 premiers utilisateurs
    print("\n--- 5 premiers utilisateurs ---")
    users = User.query.limit(5).all()
    for user in users:
        print(f"ID: {user.id}, Nom: {user.nom}, Email: {user.email}, Role: {user.role}")
    
    # Compter les entreprises
    ent_count = Entreprise.query.count()
    print(f"\nNombre d'entreprises: {ent_count}")
    
    # Lister les entreprises
    print("\n--- Entreprises ---")
    entreprises = Entreprise.query.all()
    for ent in entreprises:
        print(f"ID: {ent.id}, Nom: {ent.nom}, Statut: {ent.statut}")
    
    print("\n=== Test terminé ===")