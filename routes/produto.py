import os
from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import Produto
from database import db
from .forms import ProdutoForm

produto_bp = Blueprint('produto', __name__)

# --- ROTA: ADICIONAR PRODUTO ---
@produto_bp.route('/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_produtos():
    form = ProdutoForm()

    if request.method == 'POST' and request.form.get('precoForm'):
        try:
            val = request.form.get('precoForm').replace(',', '.')
            form.precoForm.process_data(float(val))
        except: pass

    if form.validate_on_submit():
        tags = []
        if request.form.get('c1'): tags.append('🌿 Orgânico')
        if request.form.get('c2'): tags.append('🏆 Artesanal')
        if request.form.get('c3'): tags.append('🌱 Fresco')
        if request.form.get('c4'): tags.append('🏠 Local')
        if request.form.get('c5'): tags.append('♻️ Sustentável')
        if request.form.get('c6'): tags.append('📜 Tradicional')
        
        caracteristicas_str = ",".join(tags)

        preco_original = float(form.precoForm.data)
        
        # Desconto é sempre 0 na criação
        desconto_porcentagem = 0 
        preco_final = preco_original

        novo_produto = Produto(
            nome=form.nomeForm.data,
            preco=preco_final,
            descricao=form.descricaoForm.data,
            categoria=form.categoriaForm.data,
            cidade=form.cidadeForm.data,
            usuario_id=current_user.id,
            desconto=desconto_porcentagem,
            caracteristicas=caracteristicas_str,
            nome_produtor=request.form.get('nome_produtor'),
            tempo_experiencia=request.form.get('tempo_experiencia'),
            whatsapp=request.form.get('whatsapp'),
            historia_produtor=request.form.get('historia_produtor'),
            disponibilidade=request.form.get('disponibilidade'),
            quantidade=request.form.get('quantidade'),
            unidade=request.form.get('unidade')
        )

        imagem = form.imagem.data
        if imagem:
            filename = secure_filename(imagem.filename)
            if filename:
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                imagem.save(os.path.join(upload_folder, filename))
                novo_produto.imagem = os.path.join('uploads', filename)

        try:
            db.session.add(novo_produto)
            db.session.commit()
            flash('Produto cadastrado com sucesso!', 'success')
            return redirect(url_for('main.home'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao salvar: {e}', 'error')

    return render_template('adicionar_produtos.html', form=form)

# --- ROTA: EDITAR PRODUTO ---
@produto_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_produto(id):
    produto = Produto.query.get_or_404(id)
    
    if produto.usuario_id != current_user.id:
        flash('Você não tem permissão para editar este produto.', 'error')
        return redirect(url_for('perfil.perfil'))

    form = ProdutoForm()

    if request.method == 'POST' and request.form.get('precoForm'):
        try:
            val = request.form.get('precoForm').replace(',', '.')
            form.precoForm.process_data(float(val))
        except: pass

    if form.validate_on_submit():
        # 1. Atualiza dados básicos do Form
        produto.nome = form.nomeForm.data
        produto.descricao = form.descricaoForm.data
        produto.categoria = form.categoriaForm.data
        produto.cidade = form.cidadeForm.data
        
        # 2. Recalcula Preço e Desconto (AQUI O DESCONTO EXISTE)
        preco_input = float(form.precoForm.data)
        desconto_porcentagem = int(form.descontoForm.data or 0)
        produto.desconto = desconto_porcentagem
        
        if desconto_porcentagem > 0:
            produto.preco = preco_input * (1 - (desconto_porcentagem / 100))
        else:
            produto.preco = preco_input

        # 3. Atualiza dados Manuais
        produto.nome_produtor = request.form.get('nome_produtor')
        produto.tempo_experiencia = request.form.get('tempo_experiencia')
        produto.whatsapp = request.form.get('whatsapp')
        produto.historia_produtor = request.form.get('historia_produtor')
        produto.disponibilidade = request.form.get('disponibilidade')
        produto.quantidade = request.form.get('quantidade')
        produto.unidade = request.form.get('unidade')

        # 4. Atualiza Características
        tags = []
        if request.form.get('c1'): tags.append('🌿 Orgânico')
        if request.form.get('c2'): tags.append('🏆 Artesanal')
        if request.form.get('c3'): tags.append('🌱 Fresco')
        if request.form.get('c4'): tags.append('🏠 Local')
        if request.form.get('c5'): tags.append('♻️ Sustentável')
        if request.form.get('c6'): tags.append('📜 Tradicional')
        produto.caracteristicas = ",".join(tags)

        # 5. Atualiza Imagem
        imagem = form.imagem.data
        if imagem:
            filename = secure_filename(imagem.filename)
            if filename:
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                imagem.save(os.path.join(upload_folder, filename))
                produto.imagem = os.path.join('uploads', filename)

        try:
            db.session.commit()
            flash('Produto atualizado com sucesso!', 'success')
            return redirect(url_for('perfil.perfil'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar: {e}', 'error')

    elif request.method == 'GET':
        form.nomeForm.data = produto.nome
        form.descricaoForm.data = produto.descricao
        form.categoriaForm.data = produto.categoria
        form.cidadeForm.data = produto.cidade
        form.descontoForm.data = produto.desconto
        
        if produto.desconto and produto.desconto > 0:
            preco_original_estimado = produto.preco / (1 - (produto.desconto / 100))
            form.precoForm.data = round(preco_original_estimado, 2)
        else:
            form.precoForm.data = produto.preco

    return render_template('editar_produto.html', form=form, produto=produto)

@produto_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_produto(id):
    produto = Produto.query.get_or_404(id)
    if produto.usuario_id != current_user.id:
        return redirect(url_for('main.home'))
    try:
        db.session.delete(produto)
        db.session.commit()
        flash('Produto excluído!', 'success')
    except:
        db.session.rollback()
    return redirect(url_for('perfil.perfil'))

@produto_bp.route('/buscar')
def buscar_produtos():
    busca = request.args.get('q', '')
    if busca:
        produtos = db.session.query(Produto).filter(Produto.nome.ilike(f'%{busca}%')).all()
    else:
        produtos = db.session.query(Produto).all()
    return render_template('buscar.html', produtos=produtos, busca=busca)

@produto_bp.route('/produto/<int:id>')
def pagina_produto(id):
    produto = Produto.query.get_or_404(id)
    return render_template('detalhes_produto.html', produto=produto)