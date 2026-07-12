from flask import Blueprint

products_bp = Blueprint('products', __name__)

from .routes import *  # noqa: F401, F403, E402
