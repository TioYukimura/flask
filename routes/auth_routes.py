from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from flask_mail import Message
import hashlib
import random
import string
from datetime import datetime, timedelta
from models.usuario import Usuario
from database import db

try:
    from extensions import mail
except ImportError:
    from app import mail

from .forms import LoginForm, RegistrarForm, FormEsqueciEmail, FormVerificarCodigo, FormNovaSenha

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.emailForm.data).first()
        if usuario and usuario.senha_hash == hashlib.sha256(form.senhaForm.data.encode()).hexdigest():
            login_user(usuario)
            return redirect(url_for('main.home'))
        else:
            flash('E-mail ou senha incorretos.', 'error');
    return render_template('login.html', form=form)

@auth_bp.route('/registrar', methods=['GET', 'POST'])
def registrar():
    form = RegistrarForm()
    if form.validate_on_submit():
        if Usuario.query.filter_by(email=form.emailForm.data).first():
            flash('E-mail já cadastrado.', 'error');
        else:
            novo_usuario = Usuario(
                nome=form.nomeForm.data,
                senha_hash=hashlib.sha256(form.senhaForm.data.encode()).hexdigest(),
                email=form.emailForm.data,
                cidade=form.cidadeForm.data
            )
            try:
                db.session.add(novo_usuario)
                db.session.commit()
                flash('Conta criada!', 'success');
                return redirect(url_for('auth.login'))
            except:
                db.session.rollback();
    return render_template('registrar.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu.', 'info');
    return redirect(url_for('main.home'))

@auth_bp.route('/redefinir_senha', methods=['GET', 'POST'])
def redefinir_senha():
    etapa = session.get('reset_etapa', 1)
    
    form_email = FormEsqueciEmail()
    form_codigo = FormVerificarCodigo()
    form_senha = FormNovaSenha()

    if etapa == 1 and form_email.validate_on_submit():
        email = form_email.emailForm.data
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario:
            codigo = ''.join(random.choices(string.digits, k=6))
            validade = datetime.now() + timedelta(minutes=15)
            
            session['reset_codigo'] = codigo
            session['reset_email'] = email
            session['reset_validade'] = validade.timestamp()
            
            try:
                msg = Message(
                    'Código de Recuperação - Vale & Feira',
                    sender='noreply@valefeira.com', 
                    recipients=[email]
                )
                msg.html = render_template('emails/recuperar_senha.html', 
                                            usuario=usuario, 
                                            codigo=codigo)
                mail.send(msg)
                
                flash(f'Código enviado para {email}.', 'info');
                session['reset_etapa'] = 2 
                return redirect(url_for('auth.redefinir_senha'))
                
            except Exception as e:
                print(f"Erro ao enviar email: {e}");
                flash(f'Erro ao enviar e-mail. Tente novamente.', 'error');
        else:
            flash('E-mail não encontrado.', 'error');

    elif etapa == 2 and form_codigo.validate_on_submit():
        codigo_digitado = form_codigo.codigoForm.data
        codigo_correto = session.get('reset_codigo')
        validade_timestamp = session.get('reset_validade')

        if not codigo_correto or not validade_timestamp:
            flash('Solicitação inválida. Comece novamente.', 'error');
            return redirect(url_for('auth.cancelar_recuperacao'))

        if datetime.now().timestamp() > validade_timestamp:
            flash('O código expirou (passaram-se 15 minutos).', 'error');
            return redirect(url_for('auth.cancelar_recuperacao'))

        if codigo_digitado == codigo_correto:
            flash('Código validado! Crie sua nova senha.', 'success');
            session['reset_etapa'] = 3
            return redirect(url_for('auth.redefinir_senha'))
        else:
            flash('Código incorreto.', 'error');

    elif etapa == 3 and form_senha.validate_on_submit():
        email = session.get('reset_email')
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario:
            nova_senha = form_senha.novaSenhaForm.data
            usuario.senha_hash = hashlib.sha256(nova_senha.encode()).hexdigest()
            db.session.commit()
            
            session.pop('reset_codigo', None)
            session.pop('reset_email', None)
            session.pop('reset_etapa', None)
            session.pop('reset_validade', None)
            
            flash('Senha alterada com sucesso!', 'success');
            return redirect(url_for('auth.login'))

    return render_template('redefinir_senha.html', 
                            etapa=etapa,
                            form_email=form_email,
                            form_codigo=form_codigo,
                            form_senha=form_senha)

@auth_bp.route('/cancelar_recuperacao')
def cancelar_recuperacao():
    session.pop('reset_etapa', None)
    session.pop('reset_codigo', None)
    session.pop('reset_email', None)
    session.pop('reset_validade', None)
    return redirect(url_for('auth.login'))