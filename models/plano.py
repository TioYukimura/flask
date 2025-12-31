"""
Modelos de Planos de Assinatura
"""
from datetime import datetime, timedelta
from database import db


class Plano(db.Model):
    """Modelo de plano de assinatura"""
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    duracao_dias = db.Column(db.Integer, nullable=False, default=30)
    beneficios = db.Column(db.Text, nullable=True)  # String JSON com benefícios
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento: um plano pode ter várias assinaturas
    assinaturas = db.relationship('AssinaturaUsuario', back_populates='plano')

    def __repr__(self):
        return f'<Plano {self.nome}>'


class AssinaturaUsuario(db.Model):
    """Modelo de assinatura do usuário"""
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    plano_id = db.Column(db.Integer, db.ForeignKey('plano.id'), nullable=False)
    data_inicio = db.Column(db.DateTime, default=datetime.utcnow)
    data_fim = db.Column(db.DateTime, nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    valor_pago = db.Column(db.Numeric(10, 2), nullable=False)
    metodo_pagamento = db.Column(db.String(50), nullable=False)  # 'pix' ou 'cartao'
    
    # Relacionamentos
    usuario = db.relationship('Usuario', back_populates='assinaturas')
    plano = db.relationship('Plano', back_populates='assinaturas')
    pagamentos = db.relationship('PagamentoSimulado', back_populates='assinatura')

    @property
    def esta_ativo(self):
        """Verifica se a assinatura ainda está ativa"""
        return self.ativo and self.data_fim > datetime.utcnow()
    
    @property
    def dias_restantes(self):
        """Dias restantes na assinatura"""
        if not self.esta_ativo:
            return 0
        diferenca = self.data_fim - datetime.utcnow()
        return max(0, diferenca.days)
    
    def __repr__(self):
        return f'<AssinaturaUsuario {self.usuario.email} - {self.plano.nome}>'


class PagamentoSimulado(db.Model):
    """Modelo de pagamento simulado"""
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    assinatura_id = db.Column(db.Integer, db.ForeignKey('assinatura_usuario.id'), nullable=True)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    metodo = db.Column(db.String(50), nullable=False)  # 'pix' ou 'cartao'
    status = db.Column(db.String(50), nullable=False, default='pendente')  # 'pendente', 'aprovado', 'rejeitado'
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_processamento = db.Column(db.DateTime, nullable=True)
    codigo_transacao = db.Column(db.String(100), unique=True)
    
    # Para pagamentos PIX
    dados_qr_code = db.Column(db.Text, nullable=True)
    
    # Para pagamentos com cartão (dados simulados)
    numero_cartao_mascarado = db.Column(db.String(20), nullable=True)
    
    # Relacionamentos
    usuario = db.relationship('Usuario', back_populates='pagamentos')
    assinatura = db.relationship('AssinaturaUsuario', back_populates='pagamentos')
    
    def __repr__(self):
        return f'<PagamentoSimulado {self.codigo_transacao} - {self.status}>'
