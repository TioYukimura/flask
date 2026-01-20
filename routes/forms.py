from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DecimalField, TextAreaField, FileField
from wtforms.validators import DataRequired, Email, EqualTo, NumberRange, Optional, Length

# --- Formulários de Autenticação Padrão ---
class LoginForm(FlaskForm):
    emailForm = StringField('E-mail', validators=[DataRequired(message="O e-mail é obrigatório"), Email()])
    senhaForm = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')

class RegistrarForm(FlaskForm):
    nomeForm = StringField('Nome', validators=[DataRequired()])
    emailForm = StringField('Email', validators=[DataRequired(), Email()])
    cidadeForm = StringField('Cidade', validators=[DataRequired()])
    senhaForm = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirmaSenhaForm = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('senhaForm')])
    submit = SubmitField('Registrar')

# --- Formulários das Etapas de Recuperação de Senha ---

# Etapa 1: Só o E-mail
class FormEsqueciEmail(FlaskForm):
    emailForm = StringField('Seu E-mail', validators=[DataRequired(), Email()])
    submit = SubmitField('Enviar Código')

# Etapa 2: Só o Código
class FormVerificarCodigo(FlaskForm):
    codigoForm = StringField('Código Recebido', validators=[DataRequired()])
    submit = SubmitField('Validar Código')

# Etapa 3: Só a Nova Senha
class FormNovaSenha(FlaskForm):
    novaSenhaForm = PasswordField('Nova Senha', validators=[DataRequired(), Length(min=6, message="Mínimo 6 caracteres")])
    confirmaSenhaForm = PasswordField('Confirmar', validators=[DataRequired(), EqualTo('novaSenhaForm', message='Senhas não conferem')])
    submit = SubmitField('Alterar Senha')

# --- Formulário de Produto ---
class ProdutoForm(FlaskForm):
    nomeForm = StringField('Nome', validators=[DataRequired()])
    precoForm = DecimalField('Preço', validators=[DataRequired(), NumberRange(min=0.01)])
    descontoForm = DecimalField('Desconto (%)', validators=[Optional(), NumberRange(min=0, max=60)])
    descricaoForm = TextAreaField('Descrição', validators=[DataRequired()])
    categoriaForm = StringField('Categoria', validators=[Optional()])
    cidadeForm = StringField('Cidade', validators=[Optional()])
    imagem = FileField('Imagem', validators=[Optional()])
    submit = SubmitField('Cadastrar')

# --- NOVO: Formulário de Edição de Perfil ---
class EditarPerfilForm(FlaskForm):
    nomeForm = StringField('Nome Completo', validators=[Optional()])
    cidadeForm = StringField('Cidade', validators=[Optional()])
    
    # Email com confirmação
    emailForm = StringField('Novo E-mail', validators=[Optional(), Email()])
    confirmaEmailForm = StringField('Confirmar E-mail', validators=[
        Optional(), 
        EqualTo('emailForm', message='Os e-mails não conferem')
    ])
    
    # Senha opcional (só preenche se quiser mudar)
    novaSenhaForm = PasswordField('Nova Senha (deixe em branco para não alterar)', validators=[Optional(), Length(min=6)])
    confirmaSenhaForm = PasswordField('Confirmar Nova Senha', validators=[
        EqualTo('novaSenhaForm', message='As senhas não conferem')
    ])
    
    # CAMPO OBRIGATÓRIO DE SEGURANÇA
    senha_atual = PasswordField('Sua Senha Atual (Obrigatório)', validators=[DataRequired(message="Digite sua senha atual para confirmar as mudanças")])
    
    submit = SubmitField('Salvar Alterações')