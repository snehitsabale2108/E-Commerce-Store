from flask import Blueprint

ai_bp = Blueprint('ai_assistant', __name__)

from .routes import *  # noqa: F401, F403, E402
