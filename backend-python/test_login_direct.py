# test_login_direct.py
from werkzeug.security import check_password_hash
import pymysql
from config import Config

# Connexion à la base
conn = pymysql.connect(
    host=Config.MYSQL_HOST,
    user=Config.MYSQL_USER,
    password=Config.MYSQL_PASSWORD,
    database=Config.MYSQL_DB,
    cursorclass=pymysql.cursors.DictCursor
)
cur = conn.cursor()

# Récupérer l'utilisateur
email = "admin@ged-pme.com"
password_test = "admin123"

cur.execute("SELECT id, email, password FROM users WHERE email = %s", (email,))
user = cur.fetchone()

if user:
    print(f"Utilisateur trouvé: {user['email']}")
    print(f"Hash stocké: {user['password'][:50]}...")
    
    # Vérifier le mot de passe
    is_valid = check_password_hash(user['password'], password_test)
    print(f"Mot de passe '{password_test}' est correct: {is_valid}")
    
    if not is_valid:
        print("\n⚠️ Le mot de passe est incorrect. Régénérez le hash:")
        from werkzeug.security import generate_password_hash
        new_hash = generate_password_hash(password_test)
        print(f"Nouveau hash à copier: {new_hash}")
else:
    print("❌ Utilisateur non trouvé")

cur.close()
conn.close()