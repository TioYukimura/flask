"""
Rotas de chat
"""
from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from sqlalchemy import or_, and_, desc
from database import db
from models.chat import Chat
from models.produto import Produto
from models.usuario import Usuario
from forms.chat import ChatForm

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/<int:produto_id>/<int:outro_usuario_id>', methods=['GET', 'POST'])
@login_required
def chat(produto_id, outro_usuario_id):
    """Chat entre dois usuários específicos sobre um produto"""
    produto = Produto.query.get_or_404(produto_id)
    outro_usuario = Usuario.query.get_or_404(outro_usuario_id)

    if current_user.id == outro_usuario.id:
        flash('Você não pode conversar consigo mesmo', 'error')
        return redirect(url_for('main.home'))

    if current_user.id != produto.usuario_id and outro_usuario.id != produto.usuario_id:
        flash('Pelo menos um usuário deve ser o vendedor do produto', 'error')
        return redirect(url_for('main.home'))

    form = ChatForm()

    if form.validate_on_submit():
        chat_mensagem = Chat(
            produto_id=produto_id,
            remetente_id=current_user.id,
            destinatario_id=outro_usuario_id
        )
        chat_mensagem.mensagem = form.message.data  # Criptografa automaticamente

        db.session.add(chat_mensagem)
        db.session.commit()

        flash('Mensagem enviada com sucesso!', 'success')
        return redirect(url_for('chat.chat', produto_id=produto_id, outro_usuario_id=outro_usuario_id))

    chats = Chat.query.filter(
        and_(
            Chat.produto_id == produto_id,
            or_(
                and_(Chat.remetente_id == current_user.id, Chat.destinatario_id == outro_usuario_id),
                and_(Chat.remetente_id == outro_usuario_id, Chat.destinatario_id == current_user.id)
            )
        )
    ).order_by(Chat.data_criacao.asc()).all()

    Chat.query.filter(
        and_(
            Chat.produto_id == produto_id,
            Chat.remetente_id == outro_usuario_id,
            Chat.destinatario_id == current_user.id,
            Chat.lida == False
        )
    ).update({'lida': True})
    db.session.commit()

    return render_template('chat.html',
                         form=form,
                         chats=chats,
                         produto=produto,
                         outro_usuario=outro_usuario)

@chat_bp.route('/meus_chats')
@login_required
def meus_chats():
    """Mostra todas as conversas do usuário agrupadas por parceiro"""
    todos_chats = Chat.query.filter(
        or_(Chat.remetente_id == current_user.id, Chat.destinatario_id == current_user.id)
    ).order_by(desc(Chat.data_criacao)).all()

    grupos_chat = {}
    for chat in todos_chats:
        outro_usuario_id = chat.destinatario_id if chat.remetente_id == current_user.id else chat.remetente_id
        chave = f"{chat.produto_id}_{outro_usuario_id}"

        if chave not in grupos_chat:
            grupos_chat[chave] = {
                'produto': chat.produto,
                'outro_usuario': Usuario.query.get(outro_usuario_id),
                'ultimo_chat': chat,
                'nao_lidas': 0
            }

        if chat.destinatario_id == current_user.id and not chat.lida:
            grupos_chat[chave]['nao_lidas'] += 1

    lista_grupos_chat = list(grupos_chat.values())
    lista_grupos_chat.sort(key=lambda x: x['ultimo_chat'].data_criacao, reverse=True)

    return render_template('meus_chats.html', grupos_chat=lista_grupos_chat)