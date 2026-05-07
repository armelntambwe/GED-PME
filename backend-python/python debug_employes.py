from utils.db import get_db

conn = get_db()
cursor = conn.cursor(dictionary=True)

entreprise_id = 2

cursor.execute("""
    SELECT id, nom, email, telephone, actif, date_inscription
    FROM users 
    WHERE entreprise_id = %s AND role = 'employe'
    ORDER BY id DESC
""", (entreprise_id,))

employes = cursor.fetchall()
print("Resultat:", employes)
print("Type:", type(employes))
print("Nombre:", len(employes) if employes else 0)

cursor.close()
conn.close()