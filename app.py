from flask import Flask
from extensions import db, login_manager
from routes.routes import routes

app = Flask(__name__)
app.config.from_object('config.Config')

# Inicializa as extensões
db.init_app(app)
login_manager.init_app(app)  # Certifique-se de inicializar o login_manager
login_manager.login_view = 'routes.login'  # Define a rota para redirecionar quando não autenticado

# Registra o blueprint das rotas
app.register_blueprint(routes)

# Inicializa o banco de dados na primeira execução
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
