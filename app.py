import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, g
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['UPLOAD_FOLDER'] = 'static/uploads'
DATABASE = 'admins.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def inicializar_banco():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS admins(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                tier INTEGER DEFAULT 0
            );
        ''')
        
        db.execute('''
            CREATE TABLE IF NOT EXISTS palavras(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                descricao TEXT NOT NULL,
                url TEXT NOT NULL
            );
        ''')
        db.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        db = get_db()
        try:
            db.execute('INSERT INTO admins (nome, email, senha) VALUES (?, ?, ?)', (nome, email, senha))
            db.commit()
            return redirect(url_for('index_perfil'))
        except sqlite3.IntegrityError:
            return "Erro: Email já cadastrado."
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        db = get_db()
        admin = db.execute('SELECT * FROM admins WHERE email=?', (email, )).fetchone()
        if admin and check_password_hash(admin['senha'], senha):
            session['admin_id'] = admin['id']
            session['admin_nome'] = admin['nome']
            return redirect(url_for('admin'))
        else:
            return "Login inválido."
    return render_template('login.html')

@app.route('/esqueceu_senha')
def esqueceu_senha():
    return render_template('esqueceu_senha.html')

@app.route('/admin')
def admin():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    return render_template('admin.html', nome=session['admin_nome'])

@app.route('/perfil')
def perfil():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    admin = db.execute('SELECT * FROM admins WHERE id=?', (session['admin_id'],)).fetchone()
    return render_template('perfil.html', admin=admin)

@app.route('/excluir_conta', methods=['POST'])
def excluir_conta():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    db.execute('DELETE FROM admins WHERE id=?', (session['admin_id'],))
    db.commit()
    session.clear()
    return redirect(url_for('index'))
    
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/glossario')
def glossario():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    return render_template('glossario.html')

@app.route('/cad_palavra')
def cad_palavra():
    return render_template('envio_de_video.html')


'''
.env:
SECRET_KEY=589086421acc03edf62ecb6c7750347ee66a76501d1c7510caa5392503391790
ADM_NOME=adm
ADM_EMAIL=adm@gmail.com
ADM_SENHA=adm123
'''
if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    inicializar_banco()
    with app.app_context():
        db = get_db()
        admin = db.execute('SELECT * FROM admins WHERE tier=1').fetchall()
        if not admin:
            adm_nome = os.getenv("ADM_NOME")
            adm_email = os.getenv("ADM_EMAIL")
            adm_senha = os.getenv("ADM_SENHA")
            adm_senha_segura = generate_password_hash(adm_senha)
            db.execute('INSERT INTO admins (nome, email, senha, tier) VALUES (?, ?, ?, 1)', (adm_nome, adm_email, adm_senha_segura))
            db.commit()
    app.run(debug=True)
