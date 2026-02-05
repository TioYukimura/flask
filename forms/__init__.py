# Inicialização do módulo forms# Arquivo: forms/__init__.py

# Importa os formulários gerais (que acabamos de criar em geral.py)
from .geral import (
    LoginForm, RegistrarForm, FormEsqueciEmail, FormVerificarCodigo, 
    FormNovaSenha, ProdutoForm, EditarPerfilForm, AvaliacaoForm
)

# Importa os formulários de chat e pagamento (que já existiam na pasta)
from .chat import ChatForm
from .pagamento import FormularioPagamentoPix, FormularioPagamentoCartao
