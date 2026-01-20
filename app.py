from flask import Flask
from database import db
from flask_login import LoginManager
from models import Usuario
# Importa o mail que criamos no extensions.py
from extensions import mail 

# Importa todas as rotas (incluindo o perfil agora)
from routes import auth_bp, produto_bp, main_bp, chat_bp, planos_bp, perfil_bp

app = Flask(__name__)

# --- CONFIGURAÇÕES ---
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///loja.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- CONFIGURAÇÃO DE E-MAIL (Sua configuração atual) ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
# Lembre-se de confirmar se sua senha de app está correta aqui
app.config['MAIL_USERNAME'] = 'suportevaleefeira@gmail.com' 
app.config['MAIL_PASSWORD'] = 'holx bvmh duaz cnik'

# --- INICIALIZAÇÕES ---
db.init_app(app)
mail.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = "Faça login para acessar essa página."

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# --- REGISTRO DE ROTAS (BLUEPRINTS) ---
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(produto_bp, url_prefix='/produto')
app.register_blueprint(chat_bp, url_prefix='/chat')
app.register_blueprint(planos_bp, url_prefix='/planos')
app.register_blueprint(perfil_bp, url_prefix='/perfil')  # <--- O PERFIL FOI ADICIONADO AQUI

# Cria o banco de dados se não existir
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)