# create_admin.py
from werkzeug.security import generate_password_hash

# Mot de passe que vous utiliserez pour vous connecter
password = "admin123"

# Générer le hash
hash_password = generate_password_hash(password)

print(f"Hash à copier : {hash_password}")
print(f"Email : admin@ged-pme.com")
print(f"Mot de passe original : {password}")