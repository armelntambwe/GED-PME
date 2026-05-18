import pymysql
import os

# Vérifier les tables dans ged_pme
conn = pymysql.connect(
    host='localhost',
    user='root',
    password=os.getenv('MYSQL_PASSWORD', ''),
    db='ged_pme',
    charset='utf8mb4'
)
cursor = conn.cursor()
cursor.execute('SHOW TABLES')
tables = cursor.fetchall()
print('Tables dans ged_pme:')
for table in tables:
    print(f'  - {table[0]}')

# Créer la table categories si elle n'existe pas
cursor.execute("""
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)
""")
print('Table categories créée dans ged_pme si elle n\'existait pas')

cursor.close()
conn.close()

# Maintenant vérifier ged_pme_test
conn = pymysql.connect(
    host='localhost',
    user='root',
    password=os.getenv('MYSQL_PASSWORD', ''),
    db='ged_pme_test',
    charset='utf8mb4'
)
cursor = conn.cursor()
cursor.execute('SHOW TABLES')
tables = cursor.fetchall()
print('Tables dans ged_pme_test:')
for table in tables:
    print(f'  - {table[0]}')

# Créer la table categories dans ged_pme_test aussi
cursor.execute("""
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)
""")
print('Table categories créée dans ged_pme_test si elle n\'existait pas')

cursor.close()
conn.close()

print('Vérification terminée !')