from ast import main
from models import Produto
from flask import Flask, render_template

@main.route("/") 
def home():
    
    produtos = Produto.query.all()
    
    return render_template("site.html", produtos=produtos)