from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from database import db
from models.chat import Chat
from models.usuario import Usuario
from models.produto import Produto
from forms.chat import ChatForm
from sqlalchemy import or_, and_

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/meus-chats')
@login_required
def meus_chats():
    # Na lista geral, ordenamos pelo ID decrescente para ver os mais novos primeiro
    mensagens = Chat.query.filter(
        or_(Chat.remetente_id == current_user.id, Chat.destinatario_id == current_user.id)
    ).order_by(Chat.id.desc()).all()

    chats_unicos = {}
    for msg in mensagens:
        outro_id = msg.destinatario_id if msg.remetente_id == current_user.id else msg.remetente_id
        chave = (outro_id, msg.produto_id)
        
        if chave not in chats_unicos:
            outro_usuario = Usuario.query.get(outro_id)
            produto = Produto.query.get(msg.produto_id)
            
            nao_lidas = Chat.query.filter_by(
                remetente_id=outro_id, 
                destinatario_id=current_user.id, 
                produto_id=msg.produto_id, 
                lida=False
            ).count()

            if outro_usuario and produto:
                chats_unicos[chave] = {
                    'outro_usuario': outro_usuario,
                    'produto': produto,
                    'ultima_mensagem': msg,
                    'nao_lidas': nao_lidas
                }

    return render_template('meus_chats.html', chats=chats_unicos.values())

@chat_bp.route('/chat/<int:produto_id>/<int:outro_usuario_id>', methods=['GET', 'POST'])
@login_required
def chat(produto_id, outro_usuario_id):
    form = ChatForm()
    produto = Produto.query.get_or_404(produto_id)
    outro_usuario = Usuario.query.get_or_404(outro_usuario_id)

    if request.method == 'POST' and form.validate_on_submit():
        nova_mensagem = Chat(
            remetente_id=current_user.id,
            destinatario_id=outro_usuario_id,
            produto_id=produto_id,
            mensagem=form.message.data
        )
        db.session.add(nova_mensagem)
        db.session.commit()
        return redirect(url_for('chat.chat', produto_id=produto_id, outro_usuario_id=outro_usuario_id))

    # Marca lidas
    Chat.query.filter_by(
        remetente_id=outro_usuario_id,
        destinatario_id=current_user.id,
        produto_id=produto_id,
        lida=False
    ).update({'lida': True})
    db.session.commit()

    chats = Chat.query.filter(
        Chat.produto_id == produto_id,
        or_(
            and_(Chat.remetente_id == current_user.id, Chat.destinatario_id == outro_usuario_id),
            and_(Chat.remetente_id == outro_usuario_id, Chat.destinatario_id == current_user.id)
        )
    # AQUI ESTÁ A SOLUÇÃO MÁGICA:
    # Trocamos 'data_criacao' por 'id'. O ID sempre segue a ordem cronológica real de inserção.
    ).order_by(Chat.id).all()

    return render_template('chat.html', form=form, chats=chats, produto=produto, outro_usuario=outro_usuario)

# Rota de limpeza mantida, caso você ainda queira usar
@chat_bp.route('/resetar-chat')
@login_required
def resetar_chat():
    try:
        db.session.query(Chat).delete()
        db.session.commit()
        flash('Chat limpo!', 'success')
    except Exception:
        db.session.rollback()
    return redirect(url_for('main.home'))