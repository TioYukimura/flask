from database import db
from datetime import datetime


class Avaliacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nota = db.Column(db.Integer, nullable=False)
    comentario = db.Column(db.Text, nullable=True)
    data_avaliacao = db.Column(db.DateTime, default=datetime.utcnow)

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)

    usuario = db.relationship('Usuario', backref='minhas_avaliacoes', lazy=True)


class ProdutoImagem(db.Model):
    __tablename__ = "produto_imagem"

    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)

    caminho = db.Column(db.String(255), nullable=False)

    ordem = db.Column(db.Integer, default=0)

    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ProdutoImagem produto_id={self.produto_id} ordem={self.ordem}>"


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

    desconto = db.Column(db.Integer, default=0)
    caracteristicas = db.Column(db.String(200), nullable=True)
    nome_produtor = db.Column(db.String(100), nullable=True)
    tempo_experiencia = db.Column(db.String(50), nullable=True)
    whatsapp = db.Column(db.String(20), nullable=True)
    email_contato = db.Column(db.String(120), nullable=True)
    historia_produtor = db.Column(db.Text, nullable=True)
    disponibilidade = db.Column(db.String(50), default='disponivel')
    quantidade = db.Column(db.Float, nullable=True)
    unidade = db.Column(db.String(50), nullable=True)
    destaque = db.Column(db.Boolean, default=False)
    link_mapa = db.Column(db.String(500), nullable=True)
    avaliacoes = db.relationship(
        'Avaliacao',
        backref='produto',
        lazy=True,
        cascade="all, delete-orphan"
    )

    imagens = db.relationship(
        'ProdutoImagem',
        backref='produto',
        lazy=True,
        cascade="all, delete-orphan",
        order_by="ProdutoImagem.ordem"
    )

    visualizacoes = db.Column(db.Integer, default=0)
    contatos = db.Column(db.Integer, default=0)

    @property
    def media_notas(self):
        if not self.avaliacoes:
            return 0
        soma = sum(a.nota for a in self.avaliacoes)
        return round(soma / len(self.avaliacoes), 1)

    @property
    def total_avaliacoes(self):
        return len(self.avaliacoes)

    def __repr__(self):
        return f"<Produto {self.nome}>"
