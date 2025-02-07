from .models import db, migrate
from .routes import main
from flask import Flask
from dotenv import load_dotenv, dotenv_values
from flask_cors import CORS
from .api import api

load_dotenv()

def create_app():
    app = Flask(__name__)
    config = dotenv_values()
    app.config.from_mapping(config)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    
    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(main)
    app.register_blueprint(api, prefix='/api')

    CORS(app)

    with app.app_context():
        db.create_all()
    
    return app