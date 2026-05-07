from utils.db import get_db

class User:

    @staticmethod
    def find_by_email(email):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, nom, email, password, role, actif, entreprise_id, telephone FROM users WHERE email = %s", (email,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row

    @staticmethod
    def find_by_id(user_id):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, nom, email, telephone, role, actif, entreprise_id FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row

    @staticmethod
    def create(nom, email, password_hash, role, telephone, entreprise_id):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (nom, email, password, telephone, role, actif, entreprise_id) VALUES (%s, %s, %s, %s, %s, 1, %s)", (nom, email, password_hash, telephone, role, entreprise_id))
        user_id = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()
        return user_id

    @staticmethod
    def get_employees(entreprise_id):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, nom, email, telephone, role, actif FROM users WHERE entreprise_id = %s AND role = 'employe' ORDER BY id DESC", (entreprise_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows

    @staticmethod
    def deactivate(user_id):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE users SET actif = 0 WHERE id = %s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True