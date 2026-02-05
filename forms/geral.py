# Arquivo: forms/geral.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DecimalField, TextAreaField, FileField, RadioField
from wtforms.validators import DataRequired, Email, EqualTo, NumberRange, Optional, Length

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

class FormEsqueciEmail(FlaskForm):
    emailForm = StringField('Seu E-mail', validators=[DataRequired(), Email()])
    submit = SubmitField('Enviar Código')

class FormVerificarCodigo(FlaskForm):
    codigoForm = StringField('Código Recebido', validators=[DataRequired()])
    submit = SubmitField('Validar Código')

class FormNovaSenha(FlaskForm):
    novaSenhaForm = PasswordField('Nova Senha', validators=[DataRequired(), Length(min=6, message="Mínimo 6 caracteres")])
    confirmaSenhaForm = PasswordField('Confirmar', validators=[DataRequired(), EqualTo('novaSenhaForm', message='Senhas não conferem')])
    submit = SubmitField('Alterar Senha')

class ProdutoForm(FlaskForm):
    nomeForm = StringField('Nome', validators=[DataRequired()])
    precoForm = DecimalField('Preço', validators=[DataRequired(), NumberRange(min=0.01)])
    descontoForm = DecimalField('Desconto (%)', validators=[Optional(), NumberRange(min=0, max=60)])
    descricaoForm = TextAreaField('Descrição', validators=[DataRequired()])
    categoriaForm = StringField('Categoria', validators=[Optional()])
    cidadeForm = StringField('Cidade', validators=[Optional()])
    imagem = FileField('Imagem', validators=[Optional()])
    submit = SubmitField('Cadastrar')

class EditarPerfilForm(FlaskForm):
    nomeForm = StringField('Nome Completo', validators=[Optional()])
    cidadeForm = StringField('Cidade', validators=[Optional()])
    emailForm = StringField('Novo E-mail', validators=[Optional(), Email()])
    confirmaEmailForm = StringField('Confirmar E-mail', validators=[Optional(), EqualTo('emailForm', message='Os e-mails não conferem')])
    novaSenhaForm = PasswordField('Nova Senha (deixe em branco para não alterar)', validators=[Optional(), Length(min=6)])
    confirmaSenhaForm = PasswordField('Confirmar Nova Senha', validators=[EqualTo('novaSenhaForm', message='As senhas não conferem')])
    senha_atual = PasswordField('Sua Senha Atual (Obrigatório)', validators=[DataRequired(message="Digite sua senha atual para confirmar as mudanças")])
    submit = SubmitField('Salvar Alterações')

class AvaliacaoForm(FlaskForm):
    nota = RadioField('Nota', choices=[('5','5'),('4','4'),('3','3'),('2','2'),('1','1')], validators=[DataRequired()])
    comentario = TextAreaField('Descrição (Opcional)', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Enviar Avaliação')