from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from database import db
from models.produto import Produto

relatorio_bp = Blueprint('relatorio', __name__)

@relatorio_bp.route('/painel-desempenho')
@login_required
def dashboard():
    assinatura = current_user.assinatura_atual()
    if not assinatura:
        return redirect(url_for('planos.lista_planos'))
    
    plano_nome = assinatura.plano.nome.lower()
    if 'básico' in plano_nome or 'basico' in plano_nome:
        flash('Relatórios de audiência são exclusivos para Produtores e Premium.', 'info');
        return redirect(url_for('perfil.perfil'))

    produtos = Produto.query.filter_by(usuario_id=current_user.id).all()

    total_views = sum(p.visualizacoes for p in produtos)
    total_contatos = sum(p.contatos for p in produtos)
    
    taxa_interesse = 0
    if total_views > 0:
        taxa_interesse = (total_contatos / total_views) * 100

    top_produtos = Produto.query.filter_by(usuario_id=current_user.id)\
        .order_by(Produto.visualizacoes.desc()).limit(5).all()

    labels = [p.nome for p in top_produtos]
    data_views = [p.visualizacoes for p in top_produtos]
    data_contatos = [p.contatos for p in top_produtos]

    return render_template('relatorio.html', 
                            views=total_views, 
                            contatos=total_contatos, 
                            taxa="{:.1f}".format(taxa_interesse),
                            produtos=top_produtos,
                            labels=labels,
                            data_views=data_views,
                            data_contatos=data_contatos)