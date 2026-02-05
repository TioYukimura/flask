import os
import cloudinary.uploader
from datetime import datetime

from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import case, desc, asc, func

from database import db
from models.produto import Produto, Avaliacao, ProdutoImagem
from models.chat import Chat
from models.plano import AssinaturaUsuario, Plano
from forms import ProdutoForm, AvaliacaoForm

produto_bp = Blueprint("produto", __name__)


def _salvar_imagem_cloudinary_ou_local(file_storage):
    if not file_storage or file_storage.filename == "":
        return None

    try:
        upload_result = cloudinary.uploader.upload(file_storage)
        return upload_result.get("secure_url")
    except Exception:
        pass

    nome_arquivo = secure_filename(file_storage.filename)
    caminho_pasta = os.path.join(current_app.root_path, "static", "uploads")

    if not os.path.exists(caminho_pasta):
        os.makedirs(caminho_pasta)

    caminho_completo = os.path.join(caminho_pasta, nome_arquivo)
    file_storage.save(caminho_completo)

    return f"uploads/{nome_arquivo}"


def _parse_float_ptbr(valor):
    """Converte '12,50' ou '12.50' em float com segurança."""
    if valor is None:
        return None
    valor = str(valor).strip()
    if not valor:
        return None

    if "," in valor and "." in valor:
        valor = valor.replace(".", "").replace(",", ".")
    else:
        valor = valor.replace(",", ".")

    try:
        return float(valor)
    except Exception:
        return None


def _montar_caracteristicas(request_form):
    """
    Suporta:
      - getlist('caracteristicas') (checkboxes com mesmo name)
      - c1..c6 (seu editar_produto.html atual)
    """
    lista = request_form.getlist("caracteristicas")
    if lista:
        return ",".join(lista)

    mapa = {
        "c1": "Orgânico",
        "c2": "Artesanal",
        "c3": "Fresco",
        "c4": "Local",
        "c5": "Sustentável",
        "c6": "Tradicional",
    }
    selecionadas = []
    for key, label in mapa.items():
        if request_form.get(key):
            selecionadas.append(label)

    return ",".join(selecionadas) if selecionadas else ""


@produto_bp.route("/adicionar", methods=["GET", "POST"])
@login_required
def adicionar_produtos():
    form = ProdutoForm()

    if request.method == "POST" and request.form.get("precoForm"):
        preco_float = _parse_float_ptbr(request.form.get("precoForm"))
        if preco_float is not None:
            try:
                form.precoForm.process_data(preco_float)
            except Exception:
                pass

    if form.validate_on_submit():
        caracteristicas_str = _montar_caracteristicas(request.form)

        preco_original = float(form.precoForm.data)
        desconto = int(form.descontoForm.data) if form.descontoForm.data else 0
        preco_final = preco_original * (1 - (desconto / 100))

        categoria_final = request.form.get("categoriaForm") or form.categoriaForm.data

        novo_produto = Produto(
            nome=form.nomeForm.data,
            preco=preco_final,
            desconto=desconto,
            descricao=form.descricaoForm.data,
            categoria=categoria_final,
            cidade=request.form.get("cidadeForm"),
            usuario_id=current_user.id,
            nome_produtor=request.form.get("nome_produtor"),
            tempo_experiencia=request.form.get("tempo_experiencia"),
            whatsapp=request.form.get("whatsapp"),
            email_contato=request.form.get("email_contato"),
            link_mapa=request.form.get("link_mapa"),
            historia_produtor=request.form.get("historia_produtor"),
            disponibilidade=request.form.get("disponibilidade"),
            quantidade=request.form.get("quantidade"),
            unidade=request.form.get("unidade"),
            caracteristicas=caracteristicas_str,
        )

        db.session.add(novo_produto)
        db.session.commit()

        arquivos = request.files.getlist("imagens")
        if not arquivos or (len(arquivos) == 1 and arquivos[0].filename == ""):
            arquivos = request.files.getlist("imagem")

        urls_salvas = []
        for arquivo in arquivos:
            if arquivo and arquivo.filename:
                url_img = _salvar_imagem_cloudinary_ou_local(arquivo)
                if url_img:
                    db.session.add(ProdutoImagem(produto_id=novo_produto.id, caminho=url_img, ordem=0))
                    urls_salvas.append(url_img)

        db.session.commit()

        if urls_salvas:
            novo_produto.imagem = urls_salvas[0]
            db.session.commit()

        flash("Produto cadastrado com sucesso!", "success")
        return redirect(url_for("main.home"))

    return render_template("adicionar_produtos.html", form=form)


@produto_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_produto(id):
    produto = Produto.query.get_or_404(id)

    if produto.usuario_id != current_user.id:
        flash("Acesso negado.", "error")
        return redirect(url_for("main.home"))

    form = ProdutoForm()

    if request.method == "POST" and request.form.get("precoForm"):
        preco_float = _parse_float_ptbr(request.form.get("precoForm"))
        if preco_float is not None:
            try:
                form.precoForm.process_data(preco_float)
            except Exception:
                pass

    if form.validate_on_submit():
        produto.nome = form.nomeForm.data
        produto.descricao = form.descricaoForm.data

        produto.categoria = (
            request.form.get("categoriaForm")
            or form.categoriaForm.data
            or produto.categoria
        )

        produto.link_mapa = request.form.get("link_mapa") or produto.link_mapa
        produto.cidade = request.form.get("cidadeForm") or produto.cidade

        preco_digitado = float(form.precoForm.data)
        novo_desconto = int(form.descontoForm.data) if form.descontoForm.data else 0
        produto.desconto = novo_desconto
        produto.preco = preco_digitado * (1 - (novo_desconto / 100))

        produto.nome_produtor = request.form.get("nome_produtor") or produto.nome_produtor
        produto.tempo_experiencia = request.form.get("tempo_experiencia") or produto.tempo_experiencia
        produto.whatsapp = request.form.get("whatsapp") or produto.whatsapp
        produto.historia_produtor = request.form.get("historia_produtor") or produto.historia_produtor
        produto.disponibilidade = request.form.get("disponibilidade") or produto.disponibilidade
        produto.quantidade = request.form.get("quantidade") or produto.quantidade
        produto.unidade = request.form.get("unidade") or produto.unidade

        produto.caracteristicas = _montar_caracteristicas(request.form)

        if request.form.get("remover_imagem_atual") == "1":
            imagem_antiga = produto.imagem
            produto.imagem = None

            if imagem_antiga:
                ProdutoImagem.query.filter_by(produto_id=produto.id, caminho=imagem_antiga)\
                    .delete(synchronize_session=False)

        novas = request.files.getlist("imagens")
        if not novas or (len(novas) == 1 and novas[0].filename == ""):
            novas = request.files.getlist("imagem")

        nova_url_principal = None

        max_ordem = db.session.query(func.max(ProdutoImagem.ordem))\
            .filter(ProdutoImagem.produto_id == produto.id).scalar()
        max_ordem = max_ordem if max_ordem is not None else 0

        for arquivo in novas:
            if arquivo and arquivo.filename:
                url_img = _salvar_imagem_cloudinary_ou_local(arquivo)
                if url_img:
                    max_ordem += 1
                    db.session.add(ProdutoImagem(produto_id=produto.id, caminho=url_img, ordem=max_ordem))
                    if nova_url_principal is None:
                        nova_url_principal = url_img

        if nova_url_principal:
            produto.imagem = nova_url_principal

        if not produto.imagem:
            primeira = ProdutoImagem.query.filter_by(produto_id=produto.id)\
                .order_by(ProdutoImagem.ordem.asc(), ProdutoImagem.id.asc())\
                .first()
            if primeira:
                produto.imagem = primeira.caminho

        db.session.commit()
        flash("Produto atualizado com sucesso!", "success")
        return redirect(url_for("perfil.perfil"))

    if request.method == "GET":
        form.nomeForm.data = produto.nome
        form.descricaoForm.data = produto.descricao
        form.categoriaForm.data = produto.categoria
        form.descontoForm.data = produto.desconto

        if produto.desconto and produto.desconto > 0:
            preco_original = produto.preco / (1 - (produto.desconto / 100))
            form.precoForm.data = round(preco_original, 2)
        else:
            form.precoForm.data = produto.preco

    return render_template("editar_produto.html", form=form, produto=produto)


@produto_bp.route("/destacar/<int:id>", methods=["GET", "POST"])
@login_required
def destacar_produto(id):
    produto = Produto.query.get_or_404(id)

    if produto.usuario_id != current_user.id:
        flash("Acesso negado.", "error")
        return redirect(url_for("perfil.perfil"))

    if produto.destaque:
        produto.destaque = False
        db.session.commit()
        flash(f'Destaque removido de "{produto.nome}".', "info")
        return redirect(url_for("perfil.perfil"))

    assinatura = current_user.assinatura_atual()
    if not assinatura:
        flash("Você precisa de um plano ativo para destacar produtos.", "error")
        return redirect(url_for("planos.lista_planos"))

    nome_plano = assinatura.plano.nome.lower()
    limite = 0

    if "básico" in nome_plano or "basico" in nome_plano:
        limite = 5
    elif "produtor" in nome_plano:
        limite = 20
    elif "premium" in nome_plano:
        limite = 999999

    qtd_destacados = Produto.query.filter_by(usuario_id=current_user.id, destaque=True).count()

    if qtd_destacados >= limite:
        flash("Limite de destaques atingido.", "error")
    else:
        produto.destaque = True
        db.session.commit()
        flash("Produto destacado com sucesso!", "success")

    return redirect(url_for("perfil.perfil"))


@produto_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_produto(id):
    produto = Produto.query.get_or_404(id)

    if produto.usuario_id != current_user.id:
        return redirect(url_for("main.home"))

    try:
        Chat.query.filter_by(produto_id=produto.id).delete()
        db.session.delete(produto)
        db.session.commit()
        flash("Produto removido.", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao excluir.", "error")

    return redirect(url_for("perfil.perfil"))


@produto_bp.route("/buscar")
def buscar_produtos():
    search_query = request.args.get("q", "").strip()
    categoria_filtro = request.args.get("categoria", "").strip()
    cidade_filtro = request.args.get("cidade", "").strip()
    preco_min = request.args.get("min_price", type=float)
    preco_max = request.args.get("max_price", type=float)

    agora = datetime.utcnow()

    plano_preco_sub = (
        db.session.query(
            AssinaturaUsuario.usuario_id.label("usuario_id"),
            func.max(Plano.preco).label("plano_preco"),
        )
        .join(Plano, Plano.id == AssinaturaUsuario.plano_id)
        .filter(AssinaturaUsuario.ativo == True, AssinaturaUsuario.data_fim >= agora)
        .group_by(AssinaturaUsuario.usuario_id)
        .subquery()
    )

    avaliacao_sub = (
        db.session.query(
            Avaliacao.produto_id.label("produto_id"),
            func.avg(Avaliacao.nota).label("media"),
            func.count(Avaliacao.id).label("total"),
        )
        .group_by(Avaliacao.produto_id)
        .subquery()
    )

    query = (
        db.session.query(Produto)
        .outerjoin(plano_preco_sub, plano_preco_sub.c.usuario_id == Produto.usuario_id)
        .outerjoin(avaliacao_sub, avaliacao_sub.c.produto_id == Produto.id)
    )

    if search_query:
        query = query.filter(
            Produto.nome.ilike(f"%{search_query}%")
            | Produto.descricao.ilike(f"%{search_query}%")
        )

    if categoria_filtro:
        query = query.filter(Produto.categoria == categoria_filtro)

    if cidade_filtro:
        query = query.filter(Produto.cidade.ilike(f"%{cidade_filtro}%"))

    if preco_min is not None:
        query = query.filter(Produto.preco >= preco_min)

    if preco_max is not None:
        query = query.filter(Produto.preco <= preco_max)

    destaque_rank = case((Produto.destaque == True, 1), else_=0)
    plano_preco = func.coalesce(plano_preco_sub.c.plano_preco, 0)
    nota_media = func.coalesce(avaliacao_sub.c.media, 0)

    produtos = (
        query.order_by(
            desc(destaque_rank),
            desc(plano_preco),
            desc(nota_media),
            asc(Produto.id),
        )
        .all()
    )

    categorias_db = db.session.query(Produto.categoria).distinct().all()
    categorias = [c[0] for c in categorias_db if c[0]]

    return render_template("buscar.html", produtos=produtos, busca=search_query, categorias=categorias)


@produto_bp.route("/detalhes/<int:id>")
def pagina_produto(id):
    produto = Produto.query.get_or_404(id)

    if current_user.is_authenticated and produto.usuario_id != current_user.id:
        produto.visualizacoes = (produto.visualizacoes or 0) + 1
        db.session.commit()

    form_avaliacao = AvaliacaoForm()
    return render_template("detalhes_produto.html", produto=produto, form_avaliacao=form_avaliacao)


@produto_bp.route("/avaliar/<int:produto_id>", methods=["POST"])
@login_required
def avaliar_produto(produto_id):
    form = AvaliacaoForm()
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if form.validate_on_submit():
        avaliacao_existente = Avaliacao.query.filter_by(
            usuario_id=current_user.id, produto_id=produto_id
        ).first()

        data_hoje = datetime.utcnow().strftime("%d/%m/%Y")

        if avaliacao_existente:
            avaliacao_existente.nota = int(form.nota.data)
            avaliacao_existente.comentario = form.comentario.data
            avaliacao_existente.data_avaliacao = datetime.utcnow()
            db.session.commit()
            mensagem = "Avaliação atualizada"
            tipo = "atualizacao"
        else:
            nova_avaliacao = Avaliacao(
                nota=int(form.nota.data),
                comentario=form.comentario.data,
                usuario_id=current_user.id,
                produto_id=produto_id,
            )
            db.session.add(nova_avaliacao)
            db.session.commit()
            mensagem = "Avaliação enviada"
            tipo = "nova"

        if is_ajax:
            return jsonify(
                {
                    "success": True,
                    "message": mensagem,
                    "tipo": tipo,
                    "user_nome": current_user.nome,
                    "nota": int(form.nota.data),
                    "comentario": form.comentario.data,
                    "data": data_hoje,
                }
            )

        flash(mensagem, "success")
    else:
        if is_ajax:
            return jsonify({"success": False}), 400
        flash("Erro na avaliação.", "error")

    return redirect(url_for("produto.pagina_produto", id=produto_id))
