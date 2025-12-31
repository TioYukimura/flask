from .auth_routes import auth_bp
from .produto import produto_bp
from .main import main_bp
from .chat import chat_bp
from .planos import planos_bp

__all__ = ['auth_bp', 'produto_bp', 'main_bp', 'chat_bp']