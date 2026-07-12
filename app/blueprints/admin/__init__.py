from flask import Blueprint

admin_bp = Blueprint('admin', __name__)

from .routes import *  # noqa: F401, F403, E402
