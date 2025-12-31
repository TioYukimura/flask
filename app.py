import os
from flask import Flask
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix
from database import db
from models import Usuario
from routes import auth_bp, produto_bp, main_bp, chat_bp
from routes.perfil import perfil_bp
from flask_wtf import CSRFProtect
from routes import planos_bp

app = Flask(__name__)
# Chave secreta para sessões e proteção CSRF. É mais seguro usar uma variável de ambiente.
app.secret_key = os.environ.get("SESSION_SECRET", "uma-chave-secreta-muito-segura")

# Adiciona proteção CSRF a todos os formulários
csrf = CSRFProtect(app)

# Injeta o token CSRF nos templates para que os formulários possam usá-lo
@app.context_processor
def inject_csrf_token():
    from flask_wtf.csrf import generate_csrf
    return dict(csrf_token=generate_csrf)

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///database.db")
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite de 16MB para o tamanho do arquivo

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  # Rota para a qual os usuários não autenticados são redirecionados
login_manager.login_message = 'Você precisa fazer login para acessar esta página.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp, url_prefix='/auth') # Adicionado prefixo para melhor organização
app.register_blueprint(produto_bp, url_prefix='/produto') # Adicionado prefixo
app.register_blueprint(chat_bp, url_prefix='/chat')
app.register_blueprint(perfil_bp, url_prefix='/perfil') # Adicionado prefixo
app.register_blueprint(planos_bp, url_prefix='/planos')

# Cria as tabelas do banco de dados, se não existirem
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # Executa a aplicação em modo de depuração
    app.run(debug=True, host='0.0.0.0', port=5000)