"""
Modelo de chat com criptografia automática
"""
from datetime import datetime
from database import db
from utils.crypto import encrypt_chat_message, decrypt_chat_message

class Chat(db.Model):
    """Modelo de Chat com criptografia automática"""
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    remetente_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    destinatario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    _mensagem_criptografada = db.Column('mensagem', db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    lida = db.Column(db.Boolean, default=False)

    
    produto = db.relationship('Produto', backref='chats')
    remetente = db.relationship('Usuario', foreign_keys=[remetente_id], backref='chats_enviados')
    destinatario = db.relationship('Usuario', foreign_keys=[destinatario_id], backref='chats_recebidos')

    @property
    def mensagem(self):
        """Descriptografa e retorna a mensagem"""
        return decrypt_chat_message(self._mensagem_criptografada)

    @mensagem.setter
    def mensagem(self, value):
        """Criptografa e armazena a mensagem"""
        self._mensagem_criptografada = encrypt_chat_message(value)

    def definir_mensagem_simples(self, value):
        """Define mensagem sem criptografia (para migração)"""
        self._mensagem_criptografada = value

    def obter_preview(self, max_length=50):
        """Retorna prévia da mensagem descriptografada"""
        descriptografada = self.mensagem
        if len(descriptografada) > max_length:
            return descriptografada[:max_length] + "..."
        return descriptografada

    def __repr__(self):
        return f'<Chat {self.id}: {self.obter_preview()}>'