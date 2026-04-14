# app_test.py
from flask import Flask, request, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
from config import Config
from utils.jwt_manager import generer_token

app = Flask(__name__)
app.config.from_object(Config)

def get_db():
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor
    )

# ========== PAGES HTML ==========
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register-company')
def register_page():
    return render_template('register_company.html')

@app.route('/dashboard-admin-global')
def dashboard_admin_global():
    return render_template('dashboard-admin-global.html')

@app.route('/dashboard-pme')
def dashboard_pme():
    return render_template('dashboard-admin-pme.html')

@app.route('/dashboard-employee')
def dashboard_employee():
    return render_template('dashboard-employee.html')

# ========== API ==========
@app.route('/api/register-company', methods=['POST'])
def register_company():
    data = request.json
    
    if not data or not data.get('entreprise_nom') or not data.get('email') or not data.get('password'):
        return jsonify({"success": False, "message": "Données manquantes"}), 400
    
    entreprise_nom = data['entreprise_nom']
    responsable_nom = data['responsable_nom']
    email = data['email']
    telephone = data.get('telephone', '')
    password = data['password']
    
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({"success": False, "message": "Cet email est déjà utilisé"}), 409
    
    try:
        cur.execute("""
            INSERT INTO entreprises (nom, telephone, email, statut)
            VALUES (%s, %s, %s, 'actif')
        """, (entreprise_nom, telephone, email))
        entreprise_id = cur.lastrowid
        
        password_hash = generate_password_hash(password)
        cur.execute("""
            INSERT INTO users (nom, email, password, telephone, role, actif, entreprise_id)
            VALUES (%s, %s, %s, %s, 'admin_pme', 1, %s)
        """, (responsable_nom, email, password_hash, telephone, entreprise_id))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Entreprise créée avec succès"}), 201
        
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    if not data or "email" not in data or "password" not in data:
        return jsonify({"success": False, "message": "Données manquantes"}), 400
    
    email = data["email"]
    password = data["password"]
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, nom, email, password, role, entreprise_id FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if not user:
        return jsonify({"success": False, "message": "Email non trouvé"}), 404
    
    if not check_password_hash(user['password'], password):
        return jsonify({"success": False, "message": "Mot de passe incorrect"}), 401
    
    token = generer_token(user['id'], user['role'], user.get('entreprise_id'))
    
    return jsonify({
        "success": True,
        "token": token,
        "user": {
            "id": user['id'],
            "nom": user['nom'],
            "email": user['email'],
            "role": user['role'],
            "entreprise_id": user.get('entreprise_id')
        }
    }), 200

if __name__ == '__main__':
    print("=" * 50)
    print(" GED-PME - Serveur démarré")
    print(" URL: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True)