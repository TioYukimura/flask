from database import db
from flask_login import UserMixin
import hashlib

from database import db
from flask_login import UserMixin
import hashlib

class Usuario(UserMixin, db.Model):
    """Model for user authentication and management"""
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)  # SHA-256 hash

    def __init__(self, nome, senha):
        self.nome = nome
        # gera e salva o hash da senha diretamente no campo da tabela
        self.senha_hash = hashlib.sha256(senha.encode()).hexdigest()

    def get_id(self):
        """Required by Flask-Login"""
        return str(self.id)

    def __repr__(self):
        return f'<Usuario {self.nome}>'

class Produto(db.Model):
    """Model for products in the marketplace"""
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    imagem = db.Column(db.String(255), nullable=True)  # Path to image file
    
    def __init__(self, nome, preco, descricao=None, imagem=None):
        self.nome = nome
        self.preco = preco
        self.descricao = descricao
        self.imagem = imagem
    
    @property
    def preco_formatado(self):
        """Return formatted price in Brazilian Real"""
        return f"R$ {self.preco:.2f}".replace('.', ',')
    
    def __repr__(self):
        return f'<Produto {self.nome}>'
