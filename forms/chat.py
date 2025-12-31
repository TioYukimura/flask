"""
Formulário de chat
"""
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class ChatForm(FlaskForm):
    message = TextAreaField('Mensagem', validators=[
        DataRequired(message='Mensagem é obrigatória'),
        Length(max=1000, message='Mensagem muito longa')
    ], render_kw={"rows": 3, "placeholder": "Digite sua mensagem..."})
    submit = SubmitField('Enviar')