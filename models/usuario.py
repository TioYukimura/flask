from database import db
from flask_login import UserMixin
from datetime import datetime


from database import db
from flask_login import UserMixin
from datetime import datetime


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=True)
    senha_hash = db.Column(db.String(256), nullable=False)
    cidade = db.Column(db.String(100), nullable=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    foto_perfil = db.Column(db.String(120), default='default_profile.png')

    assinaturas = db.relationship('AssinaturaUsuario', back_populates='usuario', lazy='dynamic')
    pagamentos = db.relationship('PagamentoSimulado', back_populates='usuario', lazy='dynamic')
    
    def __init__(self, nome, senha_hash, email=None, cidade=None):
        self.nome = nome
        self.senha_hash = senha_hash
        self.email = email
        self.cidade = cidade

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f'<Usuario {self.nome}>'

    
    def assinatura_atual(self):
        
        from models.plano import AssinaturaUsuario 
        
        return self.assinaturas.filter(
            AssinaturaUsuario.ativo == True,
            AssinaturaUsuario.data_fim > datetime.utcnow()
        ).order_by(AssinaturaUsuario.data_fim.desc()).first()
    
    def tem_plano_ativo(self):
        
        return self.assinatura_atual() is not None