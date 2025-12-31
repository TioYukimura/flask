from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Produto

perfil_bp = Blueprint('perfil', __name__)

@perfil_bp.route('/')
@login_required
def perfil():
    # Carrega os produtos associados ao usuário logado
    produtos = Produto.query.filter_by(usuario_id=current_user.id).all()
    return render_template('perfil.html', produtos=produtos)