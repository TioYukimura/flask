import uuid
import random
from datetime import datetime, timedelta
from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from flask_mail import Message

# Importações do projeto
from database import db
from models.plano import Plano, AssinaturaUsuario, PagamentoSimulado
from forms.pagamento import FormularioPagamentoPix, FormularioPagamentoCartao

# --- INTEGRAÇÃO MERCADO PAGO ---
from services.pagamento import gerar_pix_mercadopago, consultar_pagamento_mercadopago

# Tenta importar mail
try:
    from extensions import mail
except ImportError:
    try:
        from app import mail
    except ImportError:
        mail = None

planos_bp = Blueprint('planos', __name__)

@planos_bp.route('/')
def lista_planos():
    """Mostra os planos de assinatura disponíveis"""
    planos_disponiveis = Plano.query.filter_by(ativo=True).order_by(Plano.preco.asc()).all()
    
    assinatura_usuario = None
    if current_user.is_authenticated:
        assinatura_usuario = current_user.assinatura_atual()
    
    return render_template('planos/lista_planos.html', 
                           planos=planos_disponiveis, 
                           assinatura_usuario=assinatura_usuario)

@planos_bp.route('/assinar/<int:id_plano>', methods=['GET', 'POST'])
@login_required
def escolher_pagamento(id_plano):
    """Checkout unificado"""
    plano_escolhido = Plano.query.get_or_404(id_plano)
    
    # Verifica se usuário já possui assinatura ativa
    if current_user.tem_plano_ativo():
        flash('Você já possui um plano ativo.', 'info')
        return redirect(url_for('planos.minha_assinatura'))

    form_cartao = FormularioPagamentoCartao()
    form_pix = FormularioPagamentoPix()

    if request.method == 'POST':
        metodo = request.form.get('metodo_pagamento')
        
        # === 1. CARTÃO DE CRÉDITO (SIMULADO) ===
        if metodo == 'cartao':
            numero_cartao = request.form.get('numero') or "0000"
            
            novo_pagamento = PagamentoSimulado(
                usuario_id=current_user.id,
                valor=plano_escolhido.preco,
                metodo='cartao',
                codigo_transacao=f"CARD_{uuid.uuid4().hex[:8].upper()}",
                status='aprovado',
                numero_cartao_mascarado=f"****-{numero_cartao[-4:]}"
            )
            db.session.add(novo_pagamento)
            db.session.commit()
            
            return redirect(url_for('planos.processar_pagamento', id_pagamento=novo_pagamento.id))

        # === 2. PIX (REAL - MERCADO PAGO) ===
        elif metodo == 'pix':
            cpf_cliente = request.form.get('cpf_pix') or "19119119100"
            cpf_limpo = "".join(filter(str.isdigit, cpf_cliente))
            
            # Chama o serviço do Mercado Pago
            dados_mp = gerar_pix_mercadopago(
                valor=plano_escolhido.preco,
                descricao=f"Plano {plano_escolhido.nome} - Vale e Feira",
                email_cliente=current_user.email,
                nome_cliente=current_user.nome,
                cpf_cliente=cpf_limpo
            )
            
            if dados_mp:
                # SUCESSO! O MERCADO PAGO ACEITOU
                novo_pagamento = PagamentoSimulado(
                    usuario_id=current_user.id,
                    valor=plano_escolhido.preco,
                    metodo='pix',
                    codigo_transacao=dados_mp['id_externo'],
                    dados_qr_code=dados_mp['copia_cola'],
                    status='pendente'
                )
                
                qr_imagem = dados_mp['qr_imagem_b64']
                
                db.session.add(novo_pagamento)
                db.session.commit()
                
                return render_template('planos/pix_payment.html', 
                                     plano=plano_escolhido, 
                                     pagamento=novo_pagamento,
                                     qr_imagem=qr_imagem)
            else:
                # ERRO! O MERCADO PAGO RECUSOU
                # Isso aqui evita que a página só recarregue. Vai mostrar o erro na cara!
                return """
                <div style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: red;">❌ O MERCADO PAGO RECUSOU A CONEXÃO</h1>
                    <p style="font-size: 18px;">O seu código Python tentou gerar o PIX, mas o Mercado Pago devolveu um erro.</p>
                    <hr>
                    <p><strong>O que fazer agora?</strong></p>
                    <p>Vá no seu VS Code, olhe o <strong>TERMINAL</strong> (parte de baixo) e veja a mensagem de erro vermelha.</p>
                    <p><em>(Provavelmente você está usando a Public Key em vez do Access Token, ou o Token expirou)</em></p>
                    <br>
                    <a href="javascript:history.back()">Voltar e Tentar de Novo</a>
                </div>
                """

        # === 3. BOLETO (SIMULADO) ===
        elif metodo == 'boleto':
            data_vencimento = (datetime.now() + timedelta(days=3)).strftime('%d/%m/%Y')
            bloco_random = f"{random.randint(10000,99999)}"
            codigo_barras = f"34191.{bloco_random} 92830.{bloco_random} {int(plano_escolhido.preco*100)}"

            enviado = False
            if mail:
                try:
                    msg = Message(
                        f"Boleto Bancário - Plano {plano_escolhido.nome}", 
                        sender='noreply@valefeira.com', 
                        recipients=[current_user.email]
                    )
                    msg.html = render_template(
                        'emails/boleto_email.html', 
                        usuario=current_user, 
                        plano=plano_escolhido, 
                        codigo_barras=codigo_barras, 
                        data_vencimento=data_vencimento
                    )
                    mail.send(msg)
                    enviado = True
                except Exception as e:
                    print(f"Erro email boleto: {e}")
            
            if enviado:
                flash(f'Boleto enviado para {current_user.email}.', 'success')
            else:
                flash(f'Boleto gerado! (Erro no envio do e-mail)', 'warning')
            
            return redirect(url_for('planos.lista_planos'))

    return render_template('planos/escolher_pagamento.html', 
                           plano=plano_escolhido, 
                           form_cartao=form_cartao, 
                           form_pix=form_pix)

@planos_bp.route('/confirmar_pix/<int:id_pagamento>')
@login_required
def confirmar_pix(id_pagamento):
    pagamento = PagamentoSimulado.query.get_or_404(id_pagamento)
    status_real = consultar_pagamento_mercadopago(pagamento.codigo_transacao)
    
    if status_real == 'approved':
        return redirect(url_for('planos.processar_pagamento', id_pagamento=id_pagamento))
    elif status_real == 'pending':
        flash('Pagamento ainda em processamento pelo banco. Aguarde.', 'warning')
        return redirect(url_for('planos.lista_planos'))
    else:
        flash(f'Status do pagamento: {status_real}', 'info')
        return redirect(url_for('planos.lista_planos'))

@planos_bp.route('/processar_pagamento/<int:id_pagamento>')
@login_required
def processar_pagamento(id_pagamento):
    pagamento = PagamentoSimulado.query.get_or_404(id_pagamento)
    
    if pagamento.status == 'aprovado' and pagamento.assinatura_id:
        flash('Pagamento já processado.', 'info')
        return redirect(url_for('planos.minha_assinatura'))
    
    pagamento.status = 'aprovado'
    pagamento.data_processamento = datetime.utcnow()
    
    plano_escolhido = Plano.query.filter_by(preco=pagamento.valor).first()
    if not plano_escolhido: 
        plano_escolhido = Plano.query.first()
    
    nova_assinatura = AssinaturaUsuario(
        usuario_id=current_user.id,
        plano_id=plano_escolhido.id,
        data_fim=datetime.utcnow() + timedelta(days=plano_escolhido.duracao_dias),
        valor_pago=pagamento.valor,
        metodo_pagamento=pagamento.metodo,
        ativo=True
    )
    
    db.session.add(nova_assinatura)
    db.session.commit()
    
    pagamento.assinatura_id = nova_assinatura.id
    db.session.commit()
    
    flash(f'Sucesso! Plano {plano_escolhido.nome} ativado.', 'success')
    return redirect(url_for('planos.minha_assinatura'))

@planos_bp.route('/minha_assinatura')
@login_required
def minha_assinatura():
    assinatura_ativa = current_user.assinatura_atual()
    historico = AssinaturaUsuario.query.filter_by(usuario_id=current_user.id).order_by(AssinaturaUsuario.data_inicio.desc()).all()
    return render_template('planos/minha_assinatura.html', assinatura=assinatura_ativa, historico=historico)