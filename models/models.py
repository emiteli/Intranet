from extensions import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'users'  # Defina o nome da tabela
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.username

    def __repr__(self):
        return f'<User {self.username}>'

class Asset(db.Model):
    __tablename__ = 'assets'  # Defina o nome da tabela
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

    def __repr__(self):
        return f'<Asset {self.codigo_bem}>'  # Método de representação para facilitar a leitura

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
