import os
from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models.produto import Produto
from database import db
from .forms import ProdutoForm

produto_bp = Blueprint('produto', __name__)

# --- ADICIONAR PRODUTO ---
@produto_bp.route('/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_produtos():
    form = ProdutoForm()
    if form.validate_on_submit():
        novo_produto = Produto(
            nome=form.nomeForm.data,
            descricao=form.descricaoForm.data,
            preco=float(form.precoForm.data),
            categoria=form.categoriaForm.data,
            cidade=form.cidadeForm.data,
            usuario_id=current_user.id
        )
        
        # Upload da imagem
        imagem = form.imagem.data
        if imagem:
            filename = secure_filename(imagem.filename)
            if filename:
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)

                caminho_relativo = os.path.join('uploads', filename)  # salvo no banco
                caminho_completo = os.path.join(upload_folder, filename)  # salvo fisicamente

                imagem.save(caminho_completo)
                novo_produto.imagem = caminho_relativo

        try:
            db.session.add(novo_produto)
            db.session.commit()
            flash('Produto adicionado com sucesso!', 'success')
            return redirect(url_for('main.home'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar produto: {e}', 'error')

    return render_template('adicionar_produtos.html', form=form)


# --- EXCLUIR PRODUTO ---
@produto_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_produto(id):
    produto = Produto.query.get_or_404(id)

    if produto.usuario_id != current_user.id:
        flash('Você não tem permissão para excluir este produto.', 'error')
        return redirect(url_for('main.home'))

    try:
        if produto.imagem:
            caminho_imagem = os.path.join(current_app.root_path, 'static', produto.imagem)
            if os.path.exists(caminho_imagem):
                os.remove(caminho_imagem)

        db.session.delete(produto)
        db.session.commit()
        flash('Produto excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir produto: {e}', 'error')

    return redirect(url_for('perfil.perfil'))


# --- BUSCAR PRODUTOS ---
@produto_bp.route('/buscar')
def buscar_produtos():
    busca = request.args.get('q', '')
    if busca:
        produtos = db.session.query(Produto).filter(Produto.nome.ilike(f'%{busca}%')).all()
    else:
        produtos = db.session.query(Produto).all()  # mostra todos se não houver busca
    return render_template('buscar.html', produtos=produtos, busca=busca)


# --- PÁGINA INDIVIDUAL DO PRODUTO ---
@produto_bp.route('/produto/<int:id>')
def pagina_produto(id):
    produto = Produto.query.get_or_404(id)
    return render_template('pagina_produtos.html', produto=produto)
