import os
from flask import Flask
from .extensions import db, login_manager, mail, jwt, migrate
from .config import config


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    # Register blueprints
    from .blueprints.auth import auth_bp
    from .blueprints.products import products_bp
    from .blueprints.cart import cart_bp
    from .blueprints.orders import orders_bp
    from .blueprints.wishlist import wishlist_bp
    from .blueprints.admin import admin_bp
    from .blueprints.ai_assistant import ai_bp
    from .blueprints.main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(cart_bp, url_prefix='/cart')
    app.register_blueprint(orders_bp, url_prefix='/orders')
    app.register_blueprint(wishlist_bp, url_prefix='/wishlist')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(ai_bp, url_prefix='/ai')

    # Load user for login manager
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Context processors
    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        cart_count = 0
        wishlist_count = 0
        if current_user.is_authenticated:
            from .models import CartItem, WishlistItem
            cart_count = CartItem.query.filter_by(
                user_id=current_user.id, saved_for_later=False
            ).count()
            wishlist_count = WishlistItem.query.filter_by(
                user_id=current_user.id
            ).count()
        return {
            'app_name': app.config['APP_NAME'],
            'app_tagline': app.config['APP_TAGLINE'],
            'cart_count': cart_count,
            'wishlist_count': wishlist_count,
        }

    # Create tables
    with app.app_context():
        db.create_all()

    return app
