from flask import Blueprint

orders_bp = Blueprint('orders', __name__)

from .routes import *  # noqa: F401, F403, E402
