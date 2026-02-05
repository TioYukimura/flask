import uuid
from datetime import datetime, timedelta
from io import BytesIO

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_mail import Message
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from database import db
from extensions import mail
from models.plano import AssinaturaUsuario, PagamentoSimulado, Plano

planos_bp = Blueprint("planos", __name__)


def gerar_boleto_pdf(usuario, plano, valor, data_vencimento, cpf_pagador=None):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 14)
    c.drawString(20 * mm, height - 30 * mm, "VALE & FEIRA - Pagamento de Assinatura")

    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, height - 40 * mm, "Recibo do Pagador")

    c.setLineWidth(1)
    c.line(20 * mm, height - 45 * mm, width - 20 * mm, height - 45 * mm)

    y = height - 60 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "Beneficiário:")
    c.setFont("Helvetica", 10)
    c.drawString(50 * mm, y, "Vale & Feira Ltda - CNPJ: 00.000.000/0001-99")

    y -= 10 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "Pagador:")
    c.setFont("Helvetica", 10)

    cpf_texto = cpf_pagador if cpf_pagador else getattr(usuario, "cpf", "Não informado")
    c.drawString(50 * mm, y, f"{usuario.nome} (CPF: {cpf_texto})")

    y -= 10 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "Vencimento:")
    c.setFont("Helvetica", 10)
    c.drawString(50 * mm, y, data_vencimento.strftime("%d/%m/%Y"))

    y -= 10 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "Valor:")
    c.setFont("Helvetica", 12)
    c.drawString(50 * mm, y, f"R$ {valor:.2f}")

    y -= 10 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "Referência:")
    c.setFont("Helvetica", 10)
    c.drawString(50 * mm, y, f"Assinatura Plano {plano.nome}")

    y -= 30 * mm
    c.setFont("Helvetica", 8)
    c.drawString(20 * mm, y + 15 * mm, "Autenticação Mecânica / Ficha de Compensação")

    c.setFillColorRGB(0, 0, 0)
    c.rect(20 * mm, y, width - 40 * mm, 12 * mm, fill=1)

    c.setFillColorRGB(1, 1, 1)
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Courier-Bold", 11)
    c.drawString(
        20 * mm, y - 5 * mm, "23790.50400 90000.120004 01000.439080 1 89000000015000"
    )

    y -= 25 * mm
    c.setFont("Helvetica", 9)
    c.drawString(20 * mm, y, "Instruções:")
    c.drawString(20 * mm, y - 5 * mm, "- Pagável em qualquer banco até o vencimento.")
    c.drawString(
        20 * mm, y - 10 * mm, "- Após o vencimento, atualize o boleto no site."
    )
    c.drawString(
        20 * mm,
        y - 15 * mm,
        "- A liberação do plano ocorrerá em até 3 dias úteis após o pagamento.",
    )

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer


@planos_bp.route("/")
def lista_planos():
    planos_disponiveis = (
        Plano.query.filter_by(ativo=True).order_by(Plano.preco.asc()).all()
    )
    assinatura_usuario = None
    if current_user.is_authenticated:
        assinatura_usuario = current_user.assinatura_atual()
    return render_template(
        "planos/lista_planos.html",
        planos=planos_disponiveis,
        assinatura_usuario=assinatura_usuario,
    )


@planos_bp.route("/assinar/<int:id_plano>", methods=["GET", "POST"])
@login_required
def escolher_pagamento(id_plano):
    plano = Plano.query.get_or_404(id_plano)
    ass_atual = current_user.assinatura_atual()
    if ass_atual and ass_atual.plano_id == plano.id:
        flash("Você já possui este plano ativo.", "info")
        return redirect(url_for("perfil.perfil"))

    if request.method == "POST":
        metodo = request.form.get("metodo_pagamento")

        pix_code_fake = f"00020126580014BR.GOV.BCB.PIX0136{uuid.uuid4()}5204000053039865802BR5913VALE E FEIRA6008BRASILIA62070503***6304"

        novo_pagamento = PagamentoSimulado(
            usuario_id=current_user.id,
            valor=plano.preco,
            metodo=metodo,
            status="pendente",
            dados_qr_code=pix_code_fake,
            codigo_transacao=str(uuid.uuid4()),
        )
        db.session.add(novo_pagamento)
        db.session.commit()

        if metodo == "cartao":
            return redirect(
                url_for(
                    "planos.simular_aprovacao_banco", id_pagamento=novo_pagamento.id
                )
            )

        elif metodo == "boleto":
            cpf_digitado = request.form.get("cpf_boleto")
            vencimento = datetime.now() + timedelta(days=3)

            pdf_buffer = gerar_boleto_pdf(
                current_user, plano, plano.preco, vencimento, cpf_pagador=cpf_digitado
            )

            try:
                msg = Message(
                    subject=f"Boleto para Pagamento - Plano {plano.nome}",
                    sender="suportevaleefeira@gmail.com",
                    recipients=[current_user.email],
                )
                msg.body = f"Olá {current_user.nome},\n\nSegue em anexo o boleto para pagamento da sua assinatura.\nO plano será liberado assim que o banco confirmar o pagamento (até 3 dias úteis)."

                msg.attach(
                    f"boleto_valefeira_{novo_pagamento.id}.pdf",
                    "application/pdf",
                    pdf_buffer.getvalue(),
                )

                mail.send(msg)
                print("📧 Boleto enviado com sucesso!")
            except Exception as e:
                print(f"❌ Erro ao enviar boleto: {e}")

            return render_template(
                "planos/boleto_enviado.html", email=current_user.email
            )

        else:
            return redirect(
                url_for("planos.pix_payment", id_pagamento=novo_pagamento.id)
            )

    return render_template("planos/escolher_pagamento.html", plano=plano)


@planos_bp.route("/pagamento/pix/<int:id_pagamento>")
@login_required
def pix_payment(id_pagamento):
    pagamento = PagamentoSimulado.query.get_or_404(id_pagamento)
    if pagamento.status == "aprovado":
        flash("Pagamento já confirmado!", "success")
        return redirect(url_for("perfil.perfil"))
    plano = (
        Plano.query.filter(Plano.preco <= pagamento.valor)
        .order_by(Plano.preco.desc())
        .first()
    )
    if not plano:
        plano = Plano.query.first()
    return render_template("planos/pix_payment.html", pagamento=pagamento, plano=plano)


@planos_bp.route("/api/verificar_status/<int:id_pagamento>")
@login_required
def verificar_status_api(id_pagamento):
    pagamento = PagamentoSimulado.query.get_or_404(id_pagamento)
    resposta = {
        "status": pagamento.status,
        "aprovado": pagamento.status == "aprovado",
        "data_vencimento": "",
    }
    if pagamento.status == "aprovado" and pagamento.assinatura_id:
        assinatura = AssinaturaUsuario.query.get(pagamento.assinatura_id)
        if assinatura:
            resposta["data_vencimento"] = assinatura.data_fim.strftime("%d/%m/%Y")
    return jsonify(resposta)


@planos_bp.route("/simular_aprovacao/<int:id_pagamento>")
@login_required
def simular_aprovacao_banco(id_pagamento):
    pagamento = PagamentoSimulado.query.get_or_404(id_pagamento)
    if pagamento.status == "aprovado":
        assinatura = AssinaturaUsuario.query.get(pagamento.assinatura_id)
        if assinatura:
            return render_template(
                "planos/pagamento_aprovado.html",
                plano=assinatura.plano,
                data_vencimento=assinatura.data_fim,
            )
        return "Pagamento já processado."

    pagamento.status = "aprovado"
    pagamento.data_processamento = datetime.utcnow()
    plano = (
        Plano.query.filter(Plano.preco <= pagamento.valor)
        .order_by(Plano.preco.desc())
        .first()
    )
    if not plano:
        plano = Plano.query.first()
    data_hoje = datetime.utcnow()
    data_vencimento = data_hoje + timedelta(days=30)
    nova_assinatura = AssinaturaUsuario(
        usuario_id=pagamento.usuario_id,
        plano_id=plano.id,
        data_inicio=data_hoje,
        data_fim=data_vencimento,
        valor_pago=pagamento.valor,
        metodo_pagamento=pagamento.metodo,
        ativo=True,
    )
    db.session.add(nova_assinatura)
    db.session.flush()
    pagamento.assinatura_id = nova_assinatura.id
    db.session.commit()

    try:
        html_email = render_template(
            "emails/pagamento_confirmado.html",
            usuario=current_user,
            plano=plano,
            valor=pagamento.valor,
            data_hoje=data_hoje.strftime("%d/%m/%Y"),
            data_vencimento=data_vencimento.strftime("%d/%m/%Y"),
            codigo_transacao=pagamento.codigo_transacao,
        )
        msg = Message(
            subject=f"✅ Pagamento Confirmado - Plano {plano.nome}",
            sender="suportevaleefeira@gmail.com",
            recipients=[current_user.email],
            html=html_email,
        )
        mail.send(msg)
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")

    return render_template(
        "planos/pagamento_aprovado.html", plano=plano, data_vencimento=data_vencimento
    )


@planos_bp.route("/minha_assinatura")
@login_required
def minha_assinatura():
    assinatura = current_user.assinatura_atual()
    return render_template(
        "planos/minha_assinatura.html", assinatura_usuario=assinatura
    )


@planos_bp.route("/cancelar_assinatura", methods=["POST"])
@login_required
def cancelar_assinatura():
    assinatura = current_user.assinatura_atual()
    if assinatura:
        data_fmt = assinatura.data_fim.strftime("%d/%m/%Y")
        flash(f"Assinatura cancelada. Acesso até {data_fmt}.", "info")
    return redirect(url_for("planos.minha_assinatura"))
