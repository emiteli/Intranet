from extensions import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    profile_pic = db.Column(db.String(100), nullable=True)
    
class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filial = db.Column(db.String(50))
    grupo = db.Column(db.Integer)
    classificacao = db.Column(db.String(50))
    codigo_bem = db.Column(db.String(50), unique=True)
    item = db.Column(db.String(50))
    data_aquisicao = db.Column(db.Date)
    quantidade = db.Column(db.Integer)
    descricao_sintetica = db.Column(db.String(255))
    numero_placa = db.Column(db.String(50))
    codigo_fornecedor = db.Column(db.Integer)
    loja_fornecedor = db.Column(db.Integer)
    nota_fiscal = db.Column(db.Integer)

class Funcionario(db.Model):
    __tablename__ = 'funcionarios'
    
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), nullable=True)
    departamento = db.Column(db.String(100), nullable=True)
    nome = db.Column(db.String(150), nullable=True)
    licencas = db.Column(db.String(100), nullable=True)
    cargo = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(150), nullable=True)
    def __repr__(self):
        return f'<Funcionario {self.nome}>'
class HtmlFile(db.Model):
    __tablename__ = 'html_files'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
