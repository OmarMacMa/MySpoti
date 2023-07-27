from flask import Flask
from flask_session import Session
from .config import Config


def create_app():
    """
    Create the Flask app
    """
    app = Flask(__name__)
    app.config.from_object(Config)
    Session(app)
    return app