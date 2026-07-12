from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db


# ──────────────────────────────────────────────
# User & Address
# ──────────────────────────────────────────────

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(15), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    otp = db.Column(db.String(6), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)
    avatar = db.Column(db.String(256), default='default_avatar.png')
    diet_preference = db.Column(db.String(20), default='veg')  # veg, non_veg, vegan, jain
    language_preference = db.Column(db.String(20), default='English')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    addresses = db.relationship('Address', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    cart_items = db.relationship('CartItem', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    wishlist_items = db.relationship('WishlistItem', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'is_admin': self.is_admin,
            'avatar': self.avatar,
            'diet_preference': self.diet_preference,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<User {self.email}>'


class Address(db.Model):
    __tablename__ = 'addresses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    label = db.Column(db.String(30), default='Home')  # Home, Work, Other
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    address_line1 = db.Column(db.String(256), nullable=False)
    address_line2 = db.Column(db.String(256), nullable=True)
    city = db.Column(db.String(80), nullable=False)
    state = db.Column(db.String(80), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'label': self.label,
            'full_name': self.full_name,
            'phone': self.phone,
            'address_line1': self.address_line1,
            'address_line2': self.address_line2,
            'city': self.city,
            'state': self.state,
            'pincode': self.pincode,
            'is_default': self.is_default
        }


# ──────────────────────────────────────────────
# Category & Product
# ──────────────────────────────────────────────

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(100), nullable=True)
    image = db.Column(db.String(256), nullable=True)
    color = db.Column(db.String(20), default='#4CAF50')
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    products = db.relationship('Product', backref='category', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'icon': self.icon,
            'image': self.image,
            'color': self.color,
            'product_count': self.products.count()
        }


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    brand = db.Column(db.String(100), nullable=True)
    sku = db.Column(db.String(50), unique=True, nullable=True)

    # Pricing
    price = db.Column(db.Float, nullable=False)
    mrp = db.Column(db.Float, nullable=True)       # Maximum retail price
    discount_percent = db.Column(db.Float, default=0)

    # Stock
    stock = db.Column(db.Integer, default=0)
    min_stock_alert = db.Column(db.Integer, default=10)
    unit = db.Column(db.String(30), default='piece')  # kg, g, L, ml, piece, pack

    # Images
    image = db.Column(db.String(256), default='default_product.png')
    images = db.Column(db.Text, nullable=True)  # JSON list of image paths

    # Tags & Filters
    is_veg = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    is_trending = db.Column(db.Boolean, default=False)
    is_offer = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    tags = db.Column(db.String(500), nullable=True)  # Comma-separated

    # Nutrition info (JSON string)
    nutrition_info = db.Column(db.Text, nullable=True)

    # Ratings
    rating_avg = db.Column(db.Float, default=0.0)
    rating_count = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cart_items = db.relationship('CartItem', backref='product', lazy='dynamic')
    order_items = db.relationship('OrderItem', backref='product', lazy='dynamic')
    wishlist_items = db.relationship('WishlistItem', backref='product', lazy='dynamic')
    reviews = db.relationship('Review', backref='product', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def is_in_stock(self):
        return self.stock > 0

    @property
    def is_low_stock(self):
        return 0 < self.stock <= self.min_stock_alert

    @property
    def effective_price(self):
        if self.discount_percent:
            return round(self.price * (1 - self.discount_percent / 100), 2)
        return self.price

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'category': self.category.name if self.category else None,
            'brand': self.brand,
            'price': self.price,
            'mrp': self.mrp,
            'discount_percent': self.discount_percent,
            'effective_price': self.effective_price,
            'stock': self.stock,
            'unit': self.unit,
            'image': self.image,
            'is_veg': self.is_veg,
            'is_featured': self.is_featured,
            'is_trending': self.is_trending,
            'rating_avg': self.rating_avg,
            'rating_count': self.rating_count,
        }

    def __repr__(self):
        return f'<Product {self.name}>'


# ──────────────────────────────────────────────
# Cart
# ──────────────────────────────────────────────

class CartItem(db.Model):
    __tablename__ = 'cart_items'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    saved_for_later = db.Column(db.Boolean, default=False)

    @property
    def subtotal(self):
        return self.quantity * self.product.effective_price

    def to_dict(self):
        return {
            'id': self.id,
            'product': self.product.to_dict(),
            'quantity': self.quantity,
            'subtotal': self.subtotal,
            'saved_for_later': self.saved_for_later
        }


# ──────────────────────────────────────────────
# Wishlist
# ──────────────────────────────────────────────

class WishlistItem(db.Model):
    __tablename__ = 'wishlist_items'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)


# ──────────────────────────────────────────────
# Coupon
# ──────────────────────────────────────────────

class Coupon(db.Model):
    __tablename__ = 'coupons'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)
    discount_type = db.Column(db.String(20), default='percent')  # percent, flat
    discount_value = db.Column(db.Float, nullable=False)
    min_order_amount = db.Column(db.Float, default=0)
    max_discount_amount = db.Column(db.Float, nullable=True)
    usage_limit = db.Column(db.Integer, nullable=True)
    usage_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    valid_from = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime, nullable=True)

    def is_valid(self, order_amount):
        now = datetime.utcnow()
        if not self.is_active:
            return False, "Coupon is not active"
        if self.valid_until and now > self.valid_until:
            return False, "Coupon has expired"
        if now < self.valid_from:
            return False, "Coupon is not yet active"
        if self.usage_limit and self.usage_count >= self.usage_limit:
            return False, "Coupon usage limit reached"
        if order_amount < self.min_order_amount:
            return False, f"Minimum order amount ₹{self.min_order_amount} required"
        return True, "Valid"

    def calculate_discount(self, order_amount):
        if self.discount_type == 'percent':
            discount = order_amount * (self.discount_value / 100)
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
        else:
            discount = self.discount_value
        return round(discount, 2)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'description': self.description,
            'discount_type': self.discount_type,
            'discount_value': self.discount_value,
            'min_order_amount': self.min_order_amount,
        }


# ──────────────────────────────────────────────
# Order
# ──────────────────────────────────────────────

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'), nullable=True)

    # Status: placed, confirmed, packed, out_for_delivery, delivered, cancelled, refunded
    status = db.Column(db.String(30), default='placed')

    # Pricing
    subtotal = db.Column(db.Float, nullable=False)
    tax = db.Column(db.Float, default=0)
    delivery_fee = db.Column(db.Float, default=0)
    discount = db.Column(db.Float, default=0)
    total = db.Column(db.Float, nullable=False)

    # Payment
    payment_method = db.Column(db.String(30), default='cod')  # cod, upi, card
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, refunded
    transaction_id = db.Column(db.String(100), nullable=True)

    # Delivery
    delivery_slot = db.Column(db.String(50), nullable=True)
    estimated_delivery = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)

    # Coupon
    coupon_code = db.Column(db.String(30), nullable=True)

    # Notes
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    address = db.relationship('Address', backref='orders')
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    status_history = db.relationship('OrderStatusHistory', backref='order', lazy='dynamic',
                                     cascade='all, delete-orphan')

    STATUS_LABELS = {
        'placed': 'Order Placed',
        'confirmed': 'Confirmed',
        'packed': 'Packed',
        'out_for_delivery': 'Out for Delivery',
        'delivered': 'Delivered',
        'cancelled': 'Cancelled',
        'refunded': 'Refunded',
    }

    STATUS_ORDER = ['placed', 'confirmed', 'packed', 'out_for_delivery', 'delivered']

    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'status': self.status,
            'status_label': self.STATUS_LABELS.get(self.status, self.status),
            'subtotal': self.subtotal,
            'tax': self.tax,
            'delivery_fee': self.delivery_fee,
            'discount': self.discount,
            'total': self.total,
            'payment_method': self.payment_method,
            'payment_status': self.payment_status,
            'delivery_slot': self.delivery_slot,
            'created_at': self.created_at.isoformat(),
            'items': [item.to_dict() for item in self.items]
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)  # Snapshot
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'subtotal': self.subtotal,
            'image': self.product.image if self.product else None
        }


class OrderStatusHistory(db.Model):
    __tablename__ = 'order_status_history'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    status = db.Column(db.String(30), nullable=False)
    message = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ──────────────────────────────────────────────
# Review
# ──────────────────────────────────────────────

class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    title = db.Column(db.String(100), nullable=True)
    body = db.Column(db.Text, nullable=True)
    is_verified_purchase = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_name': self.user.name,
            'rating': self.rating,
            'title': self.title,
            'body': self.body,
            'is_verified_purchase': self.is_verified_purchase,
            'created_at': self.created_at.strftime('%d %b %Y')
        }


# ──────────────────────────────────────────────
# Banner
# ──────────────────────────────────────────────

class Banner(db.Model):
    __tablename__ = 'banners'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subtitle = db.Column(db.String(300), nullable=True)
    image = db.Column(db.String(256), nullable=True)
    link = db.Column(db.String(256), nullable=True)
    button_text = db.Column(db.String(50), default='Shop Now')
    bg_color = db.Column(db.String(20), default='#1a472a')
    text_color = db.Column(db.String(20), default='#ffffff')
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
