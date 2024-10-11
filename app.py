from flask import Flask
from extensions import db, login_manager, migrate


app = Flask(__name__)
app.config.from_object('config.Config')

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'  # Alterado aqui
migrate.init_app(app, db)


with app.app_context():
    db.create_all()

from routes.routes import routes
app.register_blueprint(routes)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
