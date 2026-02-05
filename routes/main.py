from datetime import datetime

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from flask_mail import Message
from sqlalchemy import func, desc, asc

from database import db
from extensions import mail
from models.produto import Produto, Avaliacao
from models.plano import AssinaturaUsuario, Plano

try:
    from models.usuario import Usuario
except ImportError:
    Usuario = None

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    agora = datetime.utcnow()

    plano_preco_sub = (
        db.session.query(
            AssinaturaUsuario.usuario_id.label("usuario_id"),
            func.max(Plano.preco).label("plano_preco"),
        )
        .join(Plano, Plano.id == AssinaturaUsuario.plano_id)
        .filter(AssinaturaUsuario.ativo == True, AssinaturaUsuario.data_fim >= agora)
        .group_by(AssinaturaUsuario.usuario_id)
        .subquery()
    )

    avaliacao_sub = (
        db.session.query(
            Avaliacao.produto_id.label("produto_id"),
            func.avg(Avaliacao.nota).label("media"),
        )
        .group_by(Avaliacao.produto_id)
        .subquery()
    )

    base = (
        db.session.query(Produto)
        .outerjoin(plano_preco_sub, plano_preco_sub.c.usuario_id == Produto.usuario_id)
        .outerjoin(avaliacao_sub, avaliacao_sub.c.produto_id == Produto.id)
    )

    plano_preco = func.coalesce(plano_preco_sub.c.plano_preco, 0)
    nota_media = func.coalesce(avaliacao_sub.c.media, 0)

    destaques = (
        base.filter(Produto.destaque == True)
        .order_by(desc(plano_preco), desc(nota_media), asc(Produto.id))
        .all()
    )

    faltam = 20 - len(destaques)

    restantes = []
    if faltam > 0:
        restantes = (
            base.filter((Produto.destaque == False) | (Produto.destaque.is_(None)))
            .order_by(desc(plano_preco), desc(nota_media), asc(Produto.id))
            .limit(faltam)
            .all()
        )

    produtos = (destaques + restantes)[:20]

    categorias = [
        c[0]
        for c in db.session.query(Produto.categoria).distinct().all()
        if c and c[0]
    ]
    cidades = [
        c[0] for c in db.session.query(Produto.cidade).distinct().all() if c and c[0]
    ]

    return render_template(
        "site.html",
        produtos=produtos,
        categorias=categorias,
        cidades=cidades,
        busca="",
        categoria_selecionada="",
        cidade_selecionada="",
    )


@main_bp.route("/relatar-bug", methods=["GET", "POST"])
def relatar_bug_page():
    if request.method == "POST":
        nome = request.form.get("nome")
        email_cliente = request.form.get("email")
        tipo = request.form.get("tipo_relato")
        descricao = request.form.get("descricao")

        assunto = f"[{(tipo or '').upper()}] Nova mensagem de {nome or 'Usuário'}"

        try:
            html_body = render_template(
                "emails/notificacao_bug.html",
                nome=nome,
                email=email_cliente,
                tipo=tipo,
                descricao=descricao,
                data_envio=datetime.now().strftime("%d/%m/%Y às %H:%M"),
            )

            msg = Message(
                subject=assunto,
                sender="suportevaleefeira@gmail.com",
                recipients=["suportevaleefeira@gmail.com"],
                reply_to=email_cliente,
            )

            msg.html = html_body
            msg.body = f"Nova mensagem de {nome}\n\n{descricao}"

            mail.send(msg)
            return render_template("relatar_bug.html", sucesso=True)

        except Exception as e:
            print(f"❌ ERRO AO ENVIAR EMAIL: {e}")
            flash(
                "Erro ao enviar mensagem. Tente novamente mais tarde.",
                "error",
            )

    return render_template("relatar_bug.html")


@main_bp.route("/denunciar_produto/<int:produto_id>", methods=["GET", "POST"])
@login_required
def denunciar_produto_page(produto_id):
    produto = Produto.query.get_or_404(produto_id)

    if request.method == "POST":
        nome_denunciante = request.form.get("nome")
        email_denunciante = request.form.get("email")
        motivo_selecionado = request.form.get("motivo")
        descricao = request.form.get("descricao")

        nome_vendedor = "Vendedor Desconhecido"
        email_vendedor = "Email não disponível"

        if hasattr(produto, "usuario") and getattr(produto, "usuario", None):
            nome_vendedor = produto.usuario.nome
            email_vendedor = produto.usuario.email
        elif Usuario and produto.usuario_id:
            vendedor = Usuario.query.get(produto.usuario_id)
            if vendedor:
                nome_vendedor = vendedor.nome
                email_vendedor = vendedor.email

        try:
            EMAIL_DESTINO = "suportevaleefeira@gmail.com"

            msg = Message(
                subject=f"⚠️ DENÚNCIA: Produto #{produto.id}",
                sender="noreply@valefeira.com",
                recipients=[EMAIL_DESTINO],
                reply_to=email_denunciante,
            )

            msg.html = render_template(
                "emails/notificacao_denuncia.html",
                nome_vendedor=nome_vendedor,
                email_vendedor=email_vendedor,
                produto_nome=produto.nome,
                produto_id=produto.id,
                motivo=motivo_selecionado,
                descricao=descricao,
                nome_denunciante=nome_denunciante,
                email_denunciante=email_denunciante,
                link_produto=url_for("produto.pagina_produto", id=produto.id, _external=True),
                data_envio=datetime.now().strftime("%d/%m/%Y às %H:%M"),
            )

            mail.send(msg)
            flash("Denúncia enviada com sucesso.", "success")
            return redirect(url_for("main.home"))

        except Exception as e:
            print(f"❌ ERRO AO ENVIAR DENÚNCIA: {e}")
            flash("Erro ao enviar denúncia.", "error")

    return render_template("denunciar_produto.html", produto=produto)
