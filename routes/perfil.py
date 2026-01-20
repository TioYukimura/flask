import os
import hashlib
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

# --- IMPORTS CORRIGIDOS ---
from models import Produto     
from database import db        
from .forms import EditarPerfilForm # <--- Ponto (.) indica que está na mesma pasta

perfil_bp = Blueprint('perfil', __name__)

# --- ROTA PARA EXIBIR O PERFIL ---
@perfil_bp.route('/')
@login_required
def perfil():
    # Busca apenas os produtos que esse usuário cadastrou
    produtos = Produto.query.filter_by(usuario_id=current_user.id).all()
    
    return render_template('perfil.html', produtos=produtos)

# --- NOVA ROTA: EDITAR PERFIL ---
@perfil_bp.route('/editar', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    form = EditarPerfilForm()
    
    if form.validate_on_submit():
        # 1. VERIFICAÇÃO DE SEGURANÇA (SENHA ATUAL)
        # Calcula o hash da senha digitada para comparar com o banco
        senha_atual_hash = hashlib.sha256(form.senha_atual.data.encode()).hexdigest()
        
        if senha_atual_hash != current_user.senha_hash:
            flash('Senha atual incorreta. As alterações não foram salvas.', 'error')
            return render_template('editar_perfil.html', form=form)
        
        # 2. SE A SENHA ESTIVER CERTA, APLICA AS MUDANÇAS SOLICITADAS
        alteracoes = False
        
        # Alterar Dados Pessoais (se preenchidos)
        if form.nomeForm.data and form.nomeForm.data != current_user.nome:
            current_user.nome = form.nomeForm.data
            alteracoes = True
            
        if form.cidadeForm.data and form.cidadeForm.data != current_user.cidade:
            current_user.cidade = form.cidadeForm.data
            alteracoes = True

        # Alterar Email (se preenchido e diferente do atual)
        if form.emailForm.data and form.emailForm.data != current_user.email:
            current_user.email = form.emailForm.data
            alteracoes = True
            
        # Alterar Senha (se preenchido)
        if form.novaSenhaForm.data:
            current_user.senha_hash = hashlib.sha256(form.novaSenhaForm.data.encode()).hexdigest()
            alteracoes = True
            
        if alteracoes:
            try:
                db.session.commit()
                flash('Perfil atualizado com sucesso!', 'success')
                return redirect(url_for('perfil.perfil'))
            except Exception as e:
                db.session.rollback()
                flash('Erro ao salvar no banco de dados.', 'error')
        else:
            flash('Nenhuma alteração foi feita.', 'info')
            return redirect(url_for('perfil.perfil'))
    
    # Preenche o formulário com os dados atuais do usuário ao carregar a página (GET)
    if request.method == 'GET':
        form.nomeForm.data = current_user.nome
        form.cidadeForm.data = current_user.cidade
        # Não preenchemos e-mail novo ou senha nova, para o usuário digitar se quiser mudar
        
    return render_template('editar_perfil.html', form=form)

# --- ROTA PARA UPLOAD DE FOTO ---
@perfil_bp.route('/upload_foto', methods=['POST'])
@login_required
def upload_foto():
    if 'foto' not in request.files:
        flash('Nenhuma imagem enviada.', 'error')
        return redirect(url_for('perfil.perfil'))
    
    arquivo = request.files['foto']
    
    if arquivo.filename == '':
        flash('Nenhum arquivo selecionado.', 'error')
        return redirect(url_for('perfil.perfil'))

    if arquivo:
        nome_arquivo = secure_filename(arquivo.filename)
        caminho_pasta = os.path.join(current_app.root_path, 'static', 'uploads')
        
        if not os.path.exists(caminho_pasta):
            os.makedirs(caminho_pasta)
            
        caminho_completo = os.path.join(caminho_pasta, nome_arquivo)
        arquivo.save(caminho_completo)
        
        current_user.foto_perfil = nome_arquivo
        db.session.commit()
        
        flash('Foto de perfil atualizada!', 'success')
        return redirect(url_for('perfil.perfil'))