from flask import Flask
from database import db
from flask_login import LoginManager
from models import Usuario
from extensions import mail 
from models.chat import Chat
from flask_login import current_user
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
from flask_wtf.csrf import CSRFProtect

from routes import auth_bp, produto_bp, main_bp, chat_bp, planos_bp, perfil_bp

from routes.relatorio import relatorio_bp 

app = Flask(__name__)
csrf = CSRFProtect(app)

cloudinary.config( 
    cloud_name = "deau9nkd8", 
    api_key = "841983732749958", 
    api_secret = "7RcPgkizlqF5APAR9XDXiCxowzc", 
    secure=True
)


app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///loja.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'suportevaleefeira@gmail.com' 
app.config['MAIL_PASSWORD'] = 'holx bvmh duaz cnik'


db.init_app(app)
mail.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = "Faça login para acessar essa página."

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


app.register_blueprint(main_bp)
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(produto_bp, url_prefix='/produto')
app.register_blueprint(chat_bp, url_prefix='/chat')
app.register_blueprint(planos_bp, url_prefix='/planos')
app.register_blueprint(perfil_bp, url_prefix='/perfil')


app.register_blueprint(relatorio_bp, url_prefix='/relatorio')

@app.context_processor
def inject_mensagens_nao_lidas():
    count = 0
    if current_user.is_authenticated:
       
        count = Chat.query.filter_by(destinatario_id=current_user.id, lida=False).count()
    return dict(mensagens_nao_lidas=count)


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)