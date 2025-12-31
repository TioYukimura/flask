from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from wtforms import StringField, PasswordField, SubmitField, DecimalField, TextAreaField, FileField
from wtforms.validators import DataRequired, NumberRange, Optional
from wtforms.validators import DataRequired, EqualTo, NumberRange, Optional

class LoginForm(FlaskForm):
    nomeForm = StringField('Usuário', validators=[DataRequired()])
    senhaForm = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, NumberRange, Optional

class RegistrarForm(FlaskForm):
    nomeForm = StringField('Nome', validators=[DataRequired()])
    emailForm = StringField('Email', validators=[Optional()])  # <-- agora funciona
    senhaForm = PasswordField('Senha', validators=[DataRequired()])
    cidadeForm = StringField('Cidade', validators=[DataRequired()])
    submit = SubmitField('Registrar')


class ProdutoForm(FlaskForm):
    nomeForm = StringField('Nome', validators=[DataRequired()])
    precoForm = DecimalField('Preço', validators=[DataRequired(), NumberRange(min=0.01)])
    descricaoForm = TextAreaField('Descrição', validators=[DataRequired()])
    categoriaForm = StringField('Categoria', validators=[Optional()])
    cidadeForm = StringField('Cidade', validators=[Optional()])
    imagem = FileField('Imagem', validators=[Optional()])
    submit = SubmitField('Cadastrar')
    
class RedefinirSenhaForm(FlaskForm):
    nomeForm = StringField('Usuário', validators=[DataRequired()])
    novaSenhaForm = PasswordField('Nova senha', validators=[DataRequired()])
    confirmaSenhaForm = PasswordField('Confirmar senha', validators=[DataRequired(), EqualTo('novaSenhaForm', message='As senhas devem ser iguais.')])
    submit = SubmitField('Redefinir')