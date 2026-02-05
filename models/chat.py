from datetime import datetime
from database import db
from utils.crypto import encrypt_chat_message, decrypt_chat_message


class Chat(db.Model):
    __tablename__ = "chat"

    id = db.Column(db.Integer, primary_key=True)

    produto_id = db.Column(db.Integer, db.ForeignKey("produto.id"), nullable=False)
    remetente_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    destinatario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)

    _mensagem_criptografada = db.Column("mensagem", db.Text, nullable=False)

    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    lida = db.Column(db.Boolean, default=False, nullable=False)

    produto = db.relationship("Produto", backref="chats")
    remetente = db.relationship("Usuario", foreign_keys=[remetente_id], backref="chats_enviados")
    destinatario = db.relationship("Usuario", foreign_keys=[destinatario_id], backref="chats_recebidos")

    @property
    def mensagem(self):
        return decrypt_chat_message(self._mensagem_criptografada)

    @mensagem.setter
    def mensagem(self, value):
        self._mensagem_criptografada = encrypt_chat_message(value)

    def definir_mensagem_simples(self, value):
        self._mensagem_criptografada = value

    def obter_preview(self, max_length=50):
        descriptografada = self.mensagem
        if descriptografada and len(descriptografada) > max_length:
            return descriptografada[:max_length] + "..."
        return descriptografada or ""

    def __repr__(self):
        return f"<Chat {self.id}: {self.obter_preview()}>"
