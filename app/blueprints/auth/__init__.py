from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

from .routes import *  # noqa: F401, F403, E402
