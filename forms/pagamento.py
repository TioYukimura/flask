"""
Formulários de pagamento
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, Email, Regexp


class FormularioPagamentoPix(FlaskForm):
    """Formulário de pagamento PIX"""
    
    nome_completo = StringField('Nome Completo', validators=[
        DataRequired(message='Nome completo é obrigatório'),
        Length(min=2, max=100, message='Nome deve ter entre 2 e 100 caracteres')
    ])
    
    email = StringField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Email inválido')
    ])
    
    cpf = StringField('CPF', validators=[
        DataRequired(message='CPF é obrigatório'),
        Regexp(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', message='CPF deve estar no formato XXX.XXX.XXX-XX')
    ])
    
    enviar = SubmitField('Gerar PIX')


class FormularioPagamentoCartao(FlaskForm):
    """Formulário de pagamento com cartão de crédito"""
    
    nome_titular = StringField('Nome no Cartão', validators=[
        DataRequired(message='Nome do titular é obrigatório'),
        Length(min=2, max=100, message='Nome deve ter entre 2 e 100 caracteres')
    ])
    
    numero = StringField('Número do Cartão', validators=[
        DataRequired(message='Número do cartão é obrigatório'),
        Regexp(r'^\d{4}\s?\d{4}\s?\d{4}\s?\d{4}$', message='Número do cartão inválido')
    ])
    
    validade = StringField('Validade (MM/AA)', validators=[
        DataRequired(message='Validade é obrigatória'),
        Regexp(r'^(0[1-9]|1[0-2])\/\d{2}$', message='Validade deve estar no formato MM/AA')
    ])
    
    cvv = StringField('CVV', validators=[
        DataRequired(message='CVV é obrigatório'),
        Length(min=3, max=4, message='CVV deve ter 3 ou 4 dígitos')
    ])
    
    parcelas = SelectField('Parcelas', choices=[
        ('1', '1x sem juros'),
        ('2', '2x sem juros'),
        ('3', '3x sem juros'),
        ('6', '6x com juros'),
        ('12', '12x com juros')
    ], default='1')
    
    enviar = SubmitField('Finalizar Pagamento')