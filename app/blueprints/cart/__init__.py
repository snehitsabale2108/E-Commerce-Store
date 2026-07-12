from flask import Blueprint

cart_bp = Blueprint('cart', __name__)

from .routes import *  # noqa: F401, F403, E402
