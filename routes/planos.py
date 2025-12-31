"""
Rotas de planos de assinatura
"""
import uuid
from datetime import datetime, timedelta
from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from database import db
from models.plano import Plano, AssinaturaUsuario, PagamentoSimulado
from forms.pagamento import FormularioPagamentoPix, FormularioPagamentoCartao

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

@planos_bp.route('/assinar/<int:id_plano>')
@login_required
def escolher_pagamento(id_plano):
    """Escolher método de pagamento para assinatura"""
    plano_escolhido = Plano.query.get_or_404(id_plano)
    
    # Verifica se usuário já possui assinatura ativa
    if current_user.tem_plano_ativo():
        flash('Você já possui um plano ativo', 'warning')
        return redirect(url_for('planos.minha_assinatura'))
    
    return render_template('planos/escolher_pagamento.html', plano=plano_escolhido)

@planos_bp.route('/pagar/pix/<int:id_plano>', methods=['GET', 'POST'])
@login_required
def pagar_pix(id_plano):
    """Simulação de pagamento PIX"""
    plano_escolhido = Plano.query.get_or_404(id_plano)
    formulario = FormularioPagamentoPix()
    
    if formulario.validate_on_submit():
        # Gera pagamento PIX simulado
        codigo_transacao = f"PIX_{uuid.uuid4().hex[:8].upper()}"
        dados_qr_code = f"00020126580014br.gov.bcb.pix0136{uuid.uuid4()}5204000053039865802BR5925VALE E FEIRA MARKETPLACE6009SAO PAULO62070503***6304"
        
        # Cria registro de pagamento com informações do plano
        novo_pagamento = PagamentoSimulado(
            usuario_id=current_user.id,
            valor=plano_escolhido.preco,
            metodo='pix',
            codigo_transacao=f"PIX_{plano_escolhido.id}_{uuid.uuid4().hex[:8].upper()}",
            dados_qr_code=dados_qr_code,
            status='pendente'
        )
        
        db.session.add(novo_pagamento)
        db.session.commit()
        
        return render_template('planos/pagamento_pix.html', 
                             plano=plano_escolhido, 
                             pagamento=novo_pagamento)
    
    return render_template('planos/pagar_pix.html', plano=plano_escolhido, formulario=formulario)

@planos_bp.route('/pagar/cartao/<int:id_plano>', methods=['GET', 'POST'])
@login_required
def pagar_cartao(id_plano):
    """Simulação de pagamento com cartão de crédito"""
    plano_escolhido = Plano.query.get_or_404(id_plano)
    formulario = FormularioPagamentoCartao()
    
    if formulario.validate_on_submit():
        # Simula processamento do pagamento com cartão
        numero_mascarado = f"****-****-****-{formulario.numero.data[-4:]}"
        
        # Cria registro de pagamento com informações do plano
        novo_pagamento = PagamentoSimulado(
            usuario_id=current_user.id,
            valor=plano_escolhido.preco,
            metodo='cartao',
            codigo_transacao=f"CARTAO_{plano_escolhido.id}_{uuid.uuid4().hex[:8].upper()}",
            numero_cartao_mascarado=numero_mascarado,
            status='pendente'
        )
        
        db.session.add(novo_pagamento)
        db.session.commit()
        
        # Simula aprovação imediata para pagamentos com cartão
        return redirect(url_for('planos.processar_pagamento', id_pagamento=novo_pagamento.id))
    
    return render_template('planos/pagar_cartao.html', plano=plano_escolhido, formulario=formulario)

@planos_bp.route('/confirmar_pix/<int:id_pagamento>')
@login_required
def confirmar_pix(id_pagamento):
    """Simula confirmação de pagamento PIX"""
    pagamento = PagamentoSimulado.query.get_or_404(id_pagamento)
    
    if pagamento.usuario_id != current_user.id or pagamento.status != 'pendente':
        flash('Pagamento inválido', 'error')
        return redirect(url_for('planos.lista_planos'))
    
    # Simula aprovação do pagamento PIX
    return redirect(url_for('planos.processar_pagamento', id_pagamento=id_pagamento))

@planos_bp.route('/processar_pagamento/<int:id_pagamento>')
@login_required
def processar_pagamento(id_pagamento):
    """Processa e aprova o pagamento"""
    pagamento = PagamentoSimulado.query.get_or_404(id_pagamento)
    
    if pagamento.usuario_id != current_user.id:
        flash('Acesso negado', 'error')
        return redirect(url_for('planos.lista_planos'))
    
    if pagamento.status == 'aprovado':
        flash('Pagamento já processado', 'info')
        return redirect(url_for('planos.minha_assinatura'))
    
    # Aprova o pagamento
    pagamento.status = 'aprovado'
    pagamento.data_processamento = datetime.utcnow()
    
    # Extrai o ID do plano do código de transação (formato: METODO_IDPLANO_CODIGO)
    try:
        id_plano = int(pagamento.codigo_transacao.split('_')[1])
        plano_escolhido = Plano.query.get(id_plano) or Plano.query.first()
    except:
        plano_escolhido = Plano.query.first()
    
    # Cria a assinatura
    data_vencimento = datetime.utcnow() + timedelta(days=plano_escolhido.duracao_dias)
    nova_assinatura = AssinaturaUsuario(
        usuario_id=current_user.id,
        plano_id=plano_escolhido.id,
        data_fim=data_vencimento,
        valor_pago=pagamento.valor,
        metodo_pagamento=pagamento.metodo
    )
    
    pagamento.assinatura = nova_assinatura
    
    db.session.add(nova_assinatura)
    db.session.commit()
    
    flash('Pagamento aprovado! Seu plano foi ativado.', 'success')
    return redirect(url_for('planos.minha_assinatura'))

@planos_bp.route('/minha_assinatura')
@login_required
def minha_assinatura():
    """Mostra a assinatura atual do usuário"""
    assinatura_ativa = current_user.assinatura_atual()
    historico_assinaturas = AssinaturaUsuario.query.filter_by(usuario_id=current_user.id).order_by(AssinaturaUsuario.data_inicio.desc()).all()
    
    return render_template('planos/minha_assinatura.html', 
                         assinatura=assinatura_ativa, 
                         historico=historico_assinaturas)