from database import db
from datetime import datetime

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    categoria = db.Column(db.String(50))
    cidade = db.Column(db.String(50))
    imagem = db.Column(db.String(120))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Campos Extras
    desconto = db.Column(db.Integer, default=0)
    caracteristicas = db.Column(db.String(200), nullable=True)
    nome_produtor = db.Column(db.String(100), nullable=True)
    tempo_experiencia = db.Column(db.String(50), nullable=True)
    whatsapp = db.Column(db.String(20), nullable=True)
    historia_produtor = db.Column(db.Text, nullable=True)
    disponibilidade = db.Column(db.String(50), default='disponivel')
    
    # NOVOS CAMPOS (Quantidade e Unidade)
    quantidade = db.Column(db.Float, nullable=True)
    unidade = db.Column(db.String(50), nullable=True)

    vendedor = db.relationship('Usuario', backref='produtos', lazy=True)

    def __repr__(self):
        return f'<Produto {self.nome}>'