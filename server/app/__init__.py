from flask import Flask
from config import settings
from app.api.routes import register_blueprints

def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.FLASK_SECRET_KEY
    
    register_blueprints(app)

    return app