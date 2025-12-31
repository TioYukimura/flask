from flask import Blueprint, render_template, request
from models.produto import Produto

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    busca = request.args.get('busca', '')
    categoria = request.args.get('categoria', '')
    cidade = request.args.get('cidade', '')
    
    query = Produto.query
    
    if busca:
        query = query.filter(
            (Produto.nome.contains(busca)) | 
            (Produto.descricao.contains(busca))
        )
    
    if categoria:
        query = query.filter(Produto.categoria == categoria)
    
    if cidade:
        query = query.filter(Produto.cidade == cidade)
    
    produtos = query.order_by(Produto.data_cadastro.desc()).all()
    
    categorias = Produto.query.with_entities(Produto.categoria).distinct().all()
    categorias = [c[0] for c in categorias if c[0]]  # Remove valores None
    
    cidades = Produto.query.with_entities(Produto.cidade).distinct().all()
    cidades = [c[0] for c in cidades if c[0]]  # Remove valores None
    
    return render_template('site.html', 
                         produtos=produtos, 
                         categorias=categorias, 
                         cidades=cidades,
                         busca=busca,
                         categoria_selecionada=categoria,
                         cidade_selecionada=cidade)