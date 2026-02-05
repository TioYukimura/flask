import json
import uuid

import requests

MP_ACCESS_TOKEN = (
    "TEST-3837337466092712-011711-571066f50aa60177dad7903fe532b2b0-2489253054"
)


def gerar_pix_mercadopago(
    valor, descricao, email_cliente, nome_cliente, cpf_cliente="19119119100"
):
    url = "https://api.mercadopago.com/v1/payments"

    headers = {
        "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": str(uuid.uuid4()),
    }

    print(f"--- ENVIANDO PARA MERCADO PAGO ---")
    try:
        token_usado = headers["Authorization"]

        print(f"🔍 O PYTHON ESTÁ USANDO O TOKEN: {token_usado[:20]}...")
    except:
        print("Erro ao tentar ler o token")

    email_para_api = "comprador_teste_qualquer@email.com"

    cpf_limpo = "".join(filter(str.isdigit, cpf_cliente))
    if not cpf_limpo:
        cpf_limpo = "19119119100"

    payload = {
        "transaction_amount": float(valor),
        "description": descricao,
        "payment_method_id": "pix",
        "payer": {
            "email": email_para_api,
            "first_name": "Cliente",
            "last_name": "Teste",
            "identification": {"type": "CPF", "number": cpf_limpo},
        },
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()

        print(f"Status Code: {response.status_code}")

        if response.status_code == 201:
            print("✅ SUCESSO! PIX CRIADO.")
            return {
                "id_externo": str(data["id"]),
                "copia_cola": data["point_of_interaction"]["transaction_data"][
                    "qr_code"
                ],
                "qr_imagem_b64": data["point_of_interaction"]["transaction_data"][
                    "qr_code_base64"
                ],
                "status": data["status"],
            }
        else:
            print("❌ ERRO DA API:")
            print(json.dumps(data, indent=2))
            return None

    except Exception as e:
        print(f"❌ ERRO DE CONEXÃO: {e}")
        return None


def consultar_pagamento_mercadopago(id_pagamento_externo):
    url = f"https://api.mercadopago.com/v1/payments/{id_pagamento_externo}"
    headers = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()["status"]
    except Exception as e:
        print(f"Erro consulta: {e}")

    return None
