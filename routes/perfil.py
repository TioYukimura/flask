import os
import hashlib
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from models.produto import Produto     
from models.plano import AssinaturaUsuario
from database import db        
from .forms import EditarPerfilForm 

perfil_bp = Blueprint('perfil', __name__)

@perfil_bp.route('/')
@login_required
def perfil():
    produtos = Produto.query.filter_by(usuario_id=current_user.id).all()
    
    assinatura = current_user.assinatura_atual()
    
    nome_plano = "Gratuito"
    limite_destaques = 0
    destaque_usados = 0

    if assinatura:
        nome_plano = assinatura.plano.nome
        
        nome_lower = nome_plano.lower()
        if 'básico' in nome_lower or 'basico' in nome_lower:
            limite_destaques = 5
        elif 'produtor' in nome_lower:
            limite_destaques = 20
        elif 'premium' in nome_lower:
            limite_destaques = 999 
            
        destaque_usados = Produto.query.filter_by(usuario_id=current_user.id, destaque=True).count()

    return render_template('perfil.html', 
                            produtos=produtos, 
                            assinatura=assinatura,
                            nome_plano=nome_plano,
                            limite=limite_destaques,
                            usados=destaque_usados)

@perfil_bp.route('/editar', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    form = EditarPerfilForm()
    
    if form.validate_on_submit():
        senha_atual_hash = hashlib.sha256(form.senha_atual.data.encode()).hexdigest()
        
        if senha_atual_hash != current_user.senha_hash:
            flash('Senha atual incorreta.', 'error');
            return render_template('editar_perfil.html', form=form)
        
        alteracoes = False
        
        if form.nomeForm.data and form.nomeForm.data != current_user.nome:
            current_user.nome = form.nomeForm.data
            alteracoes = True
            
        if form.cidadeForm.data and form.cidadeForm.data != current_user.cidade:
            current_user.cidade = form.cidadeForm.data
            alteracoes = True

        if form.emailForm.data and form.emailForm.data != current_user.email:
            current_user.email = form.emailForm.data
            alteracoes = True
            
        if form.novaSenhaForm.data:
            current_user.senha_hash = hashlib.sha256(form.novaSenhaForm.data.encode()).hexdigest()
            alteracoes = True
            
        if alteracoes:
            try:
                db.session.commit()
                flash('Perfil atualizado com sucesso!', 'success');
                return redirect(url_for('perfil.perfil'))
            except:
                db.session.rollback()
                flash('Erro ao salvar.', 'error');
        else:
            flash('Nenhuma alteração realizada.', 'info');
            return redirect(url_for('perfil.perfil'))
    
    if request.method == 'GET':
        form.nomeForm.data = current_user.nome
        form.cidadeForm.data = current_user.cidade
        
    return render_template('editar_perfil.html', form=form)

@perfil_bp.route('/upload_foto', methods=['POST'])
@login_required
def upload_foto():
    if 'foto' not in request.files:
        return redirect(url_for('perfil.perfil'))
    
    arquivo = request.files['foto']
    
    if arquivo.filename == '':
        return redirect(url_for('perfil.perfil'))

    if arquivo:
        nome_arquivo = secure_filename(arquivo.filename)
        caminho_pasta = os.path.join(current_app.root_path, 'static', 'uploads')
        
        if not os.path.exists(caminho_pasta):
            os.makedirs(caminho_pasta)
            
        arquivo.save(os.path.join(caminho_pasta, nome_arquivo))
        
        current_user.foto_perfil = nome_arquivo
        db.session.commit()
        
        flash('Foto atualizada!', 'success');
        return redirect(url_for('perfil.perfil'))