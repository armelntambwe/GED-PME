# database/init_db.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app, mysql

def init_database():
    with app.app_context():
        cur = mysql.connection.cursor()
        
        # Table users
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nom VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role ENUM('admin_global', 'admin_pme', 'employe') DEFAULT 'employe',
                telephone VARCHAR(20),
                date_inscription DATETIME DEFAULT CURRENT_TIMESTAMP,
                actif BOOLEAN DEFAULT TRUE
            )
        """)
        
        # Table documents
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INT AUTO_INCREMENT PRIMARY KEY,
                titre VARCHAR(200) NOT NULL,
                description TEXT,
                fichier_nom VARCHAR(255),
                fichier_chemin VARCHAR(255),
                fichier_taille INT,
                date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
                statut ENUM('brouillon', 'soumis', 'valide', 'rejete', 'archive') DEFAULT 'brouillon',
                auteur_id INT NOT NULL,
                categorie_id INT,
                validateur_id INT,
                date_validation DATETIME,
                commentaire_rejet TEXT,
                FOREIGN KEY (auteur_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Table categories
        cur.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nom VARCHAR(50) UNIQUE NOT NULL,
                description TEXT,
                date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table logs
        cur.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                action VARCHAR(100) NOT NULL,
                description TEXT,
                date DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_id INT NOT NULL,
                document_id INT,
                adresse_ip VARCHAR(45),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        mysql.connection.commit()
        cur.close()
        print("✅ Tables créées avec succès!")

if __name__ == "__main__":
    init_database()