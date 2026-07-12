from flask import Blueprint

wishlist_bp = Blueprint('wishlist', __name__)

from .routes import *  # noqa: F401, F403, E402
