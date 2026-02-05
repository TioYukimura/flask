from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy import or_, and_

from database import db
from models.chat import Chat
from models.usuario import Usuario
from models.produto import Produto
from forms.chat import ChatForm

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/meus-chats")
@login_required
def meus_chats():
    mensagens = (
        Chat.query.filter(
            or_(
                Chat.remetente_id == current_user.id,
                Chat.destinatario_id == current_user.id,
            )
        )
        .order_by(Chat.id.desc())
        .all()
    )

    chats_unicos = {}
    for msg in mensagens:
        outro_id = (
            msg.destinatario_id
            if msg.remetente_id == current_user.id
            else msg.remetente_id
        )
        chave = (outro_id, msg.produto_id)

        if chave not in chats_unicos:
            outro_usuario = Usuario.query.get(outro_id)
            produto = Produto.query.get(msg.produto_id)

            if not outro_usuario or not produto:
                continue

            nao_lidas = (
                Chat.query.filter_by(
                    remetente_id=outro_id,
                    destinatario_id=current_user.id,
                    produto_id=msg.produto_id,
                    lida=False,
                ).count()
            )

            chats_unicos[chave] = {
                "outro_usuario": outro_usuario,
                "produto": produto,
                "ultima_mensagem": msg,
                "nao_lidas": nao_lidas,
            }

    return render_template("meus_chats.html", chats=list(chats_unicos.values()))


@chat_bp.route("/chat/<int:produto_id>/<int:outro_usuario_id>", methods=["GET", "POST"])
@login_required
def chat(produto_id, outro_usuario_id):
    form = ChatForm()
    produto = Produto.query.get_or_404(produto_id)
    outro_usuario = Usuario.query.get_or_404(outro_usuario_id)

    if outro_usuario.id == current_user.id:
        flash("Você não pode abrir um chat com você mesmo.", "error")
        return redirect(url_for("chat.meus_chats"))

    if request.method == "GET" and current_user.id != produto.usuario_id:
        ja_conversou = (
            Chat.query.filter(
                Chat.produto_id == produto_id,
                or_(
                    and_(
                        Chat.remetente_id == current_user.id,
                        Chat.destinatario_id == outro_usuario_id,
                    ),
                    and_(
                        Chat.remetente_id == outro_usuario_id,
                        Chat.destinatario_id == current_user.id,
                    ),
                ),
            )
            .first()
        )

        if not ja_conversou:
            produto.contatos = (produto.contatos or 0) + 1
            db.session.commit()

    if request.method == "POST" and form.validate_on_submit():
        texto = (form.message.data or "").strip()
        if texto:
            nova_mensagem = Chat(
                remetente_id=current_user.id,
                destinatario_id=outro_usuario_id,
                produto_id=produto_id,
                mensagem=texto,
                lida=False,
            )
            db.session.add(nova_mensagem)
            db.session.commit()

        return redirect(url_for("chat.chat", produto_id=produto_id, outro_usuario_id=outro_usuario_id))

    Chat.query.filter_by(
        remetente_id=outro_usuario_id,
        destinatario_id=current_user.id,
        produto_id=produto_id,
        lida=False,
    ).update({"lida": True})
    db.session.commit()

    chats = (
        Chat.query.filter(
            Chat.produto_id == produto_id,
            or_(
                and_(
                    Chat.remetente_id == current_user.id,
                    Chat.destinatario_id == outro_usuario_id,
                ),
                and_(
                    Chat.remetente_id == outro_usuario_id,
                    Chat.destinatario_id == current_user.id,
                ),
            ),
        )
        .order_by(Chat.id.asc())
        .all()
    )

    mensagens_nao_lidas = (
        Chat.query.filter_by(destinatario_id=current_user.id, lida=False).count()
    )

    return render_template(
        "chat.html",
        form=form,
        chats=chats,
        produto=produto,
        outro_usuario=outro_usuario,
        mensagens_nao_lidas=mensagens_nao_lidas,
    )


@chat_bp.route("/chats/excluir/<int:produto_id>/<int:outro_usuario_id>", methods=["POST"])
@login_required
def excluir_chat(produto_id, outro_usuario_id):
    outro_usuario = Usuario.query.get(outro_usuario_id)
    if not outro_usuario:
        flash("Usuário não encontrado.", "error")
        return redirect(url_for("chat.meus_chats"))


    try:
        deletados = (
            Chat.query.filter(
                Chat.produto_id == produto_id,
                or_(
                    and_(
                        Chat.remetente_id == current_user.id,
                        Chat.destinatario_id == outro_usuario_id,
                    ),
                    and_(
                        Chat.remetente_id == outro_usuario_id,
                        Chat.destinatario_id == current_user.id,
                    ),
                ),
            )
            .delete(synchronize_session=False)
        )
        db.session.commit()

        if deletados == 0:
            flash("Nenhuma conversa encontrada para excluir.", "error")
        else:
            flash("Conversa excluída com sucesso.", "success")

    except Exception:
        db.session.rollback()
        flash("Erro ao excluir a conversa. Tente novamente.", "error")

    return redirect(url_for("chat.meus_chats"))


@chat_bp.route("/resetar-chat")
@login_required
def resetar_chat():
    try:
        db.session.query(Chat).delete()
        db.session.commit()
        flash("Chat limpo!", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao limpar o chat.", "error")

    return redirect(url_for("main.home"))
