from database import db
from flask_login import UserMixin
import hashlib
from datetime import datetime


class Usuario(UserMixin, db.Model):
    """Modelo para autenticação e gestão de usuários"""
    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)  # SHA-256 hash
    cidade = db.Column(db.String(100), nullable=True)
    foto_perfil = db.Column(db.String(200), nullable=True, default='default_perfil.png')

    # Relacionamento: Um usuário pode ter vários produtos
    produtos = db.relationship('Produto', backref='dono', lazy=True)

    def __init__(self, nome, senha, cidade=None):
        self.nome = nome
        self.cidade = cidade
        # gera e salva o hash da senha
        self.senha_hash = hashlib.sha256(senha.encode()).hexdigest()

    def verificar_senha(self, senha):
        """Verifica se a senha digitada corresponde ao hash"""
        hash_digitado = hashlib.sha256(senha.encode()).hexdigest()
        return self.senha_hash == hash_digitado

    def __repr__(self):
        return f'<Usuario {self.nome}>'


class Produto(db.Model):
    """Modelo para produtos no marketplace"""
    __tablename__ = 'produto'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    imagem = db.Column(db.String(255), nullable=True)  # Caminho do arquivo
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

    # Chave Estrangeira: liga o produto ao usuário (vendedor)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

    def __init__(self, nome, preco, usuario_id, descricao=None, imagem=None):
        self.nome = nome
        self.preco = preco
        self.usuario_id = usuario_id
        self.descricao = descricao
        self.imagem = imagem

    @property
    def preco_formatado(self):
        """Retorna o preço formatado em Real"""
        return f"R$ {self.preco:.2f}".replace('.', ',')

    def __repr__(self):
        return f'<Produto {self.nome}>'