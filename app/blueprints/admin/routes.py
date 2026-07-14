from flask import render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
import os
import csv
import io
from ...extensions import db
from ...models import (User, Product, Category, Order, OrderItem,
                       OrderStatusHistory, Coupon, Banner)
from sqlalchemy import func
from . import admin_bp


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@admin_bp.route('/')
@admin_required
def dashboard():
    # Sales analytics
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    total_revenue = db.session.query(func.sum(Order.total)).filter(
        Order.status != 'cancelled'
    ).scalar() or 0

    today_revenue = db.session.query(func.sum(Order.total)).filter(
        func.date(Order.created_at) == today,
        Order.status != 'cancelled'
    ).scalar() or 0

    total_orders = Order.query.count()
    pending_orders = Order.query.filter(Order.status.in_(['placed', 'confirmed', 'packed'])).count()
    total_customers = User.query.filter_by(is_admin=False).count()
    total_products = Product.query.count()
    low_stock = Product.query.filter(Product.stock <= Product.min_stock_alert, Product.stock > 0).count()
    out_of_stock = Product.query.filter_by(stock=0, is_active=True).count()

    # Daily revenue chart (last 7 days)
    daily_data = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        rev = db.session.query(func.sum(Order.total)).filter(
            func.date(Order.created_at) == d,
            Order.status != 'cancelled'
        ).scalar() or 0
        daily_data.append({'date': d.strftime('%d %b'), 'revenue': float(rev)})

    # Top selling products
    top_products = db.session.query(
        Product.name, func.sum(OrderItem.quantity).label('qty')
    ).join(OrderItem).group_by(Product.id).order_by(func.sum(OrderItem.quantity).desc()).limit(5).all()

    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()

    # Order status breakdown
    status_counts = db.session.query(
        Order.status, func.count(Order.id)
    ).group_by(Order.status).all()

    return render_template('admin/dashboard.html',
                           total_revenue=total_revenue,
                           today_revenue=today_revenue,
                           total_orders=total_orders,
                           pending_orders=pending_orders,
                           total_customers=total_customers,
                           total_products=total_products,
                           low_stock=low_stock,
                           out_of_stock=out_of_stock,
                           daily_data=daily_data,
                           top_products=top_products,
                           recent_orders=recent_orders,
                           status_counts=dict(status_counts))


@admin_bp.route('/products')
@admin_required
def products():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '')
    category_id = request.args.get('category', '', type=str)
    query = Product.query
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    if category_id:
        query = query.filter_by(category_id=int(category_id))
    products = query.order_by(Product.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    categories = Category.query.all()
    return render_template('admin/products.html', products=products, categories=categories, search=search)

def _compute_discount(price, mrp):
    """Discount % is always derived from MRP and Selling Price, so it can
    never drift out of sync with what the customer is actually charged."""
    if mrp and mrp > 0 and price <= mrp:
        return round((1 - price / mrp) * 100, 1)
    return 0.0

@admin_bp.route('/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    categories = Category.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        import json
        from werkzeug.utils import secure_filename
        name = request.form.get('name', '').strip()
        slug = name.lower().replace(' ', '-').replace('/', '-')

        # Check unique slug
        existing = Product.query.filter_by(slug=slug).first()
        if existing:
            slug = slug + '-' + str(Product.query.count() + 1)

        # Handle image upload
        image_filename = 'default_product.png'
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_path = os.path.join(current_app.root_path, 'static/images/products', filename)
                file.save(upload_path)
                image_filename = filename

        product = Product(
            name=name,
            slug=slug,
            description=request.form.get('description', ''),
            category_id=int(request.form.get('category_id')),
            brand=request.form.get('brand', ''),
            sku=request.form.get('sku', ''),
            price=float(request.form.get('price', 0)),
            mrp=float(request.form.get('mrp', 0)) or None,
            discount_percent=_compute_discount(float(request.form.get('price', 0)), float(request.form.get('mrp', 0)) or 0),
            stock=int(request.form.get('stock', 0)),
            rating_avg=float(request.form.get('rating_avg', 0) or 0),
            rating_count=int(request.form.get('rating_count', 0) or 0),
            unit=request.form.get('unit', 'piece'),
            image=image_filename,
            is_veg=request.form.get('is_veg') == 'true',
            is_featured=bool(request.form.get('is_featured')),
            is_trending=bool(request.form.get('is_trending')),
            is_offer=bool(request.form.get('is_offer')),
            tags=request.form.get('tags', ''),
            nutrition_info=request.form.get('nutrition_info', '{}'),
        )
        db.session.add(product)
        db.session.commit()
        flash(f'Product "{name}" added successfully!', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/product_form.html', product=None, categories=categories)


@admin_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    categories = Category.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        from werkzeug.utils import secure_filename
        product.name = request.form.get('name', product.name).strip()
        product.description = request.form.get('description', product.description)
        product.category_id = int(request.form.get('category_id', product.category_id))
        product.brand = request.form.get('brand', product.brand)
        product.price = float(request.form.get('price', product.price))
        product.mrp = float(request.form.get('mrp', 0)) or None
        product.discount_percent = _compute_discount(product.price, product.mrp or 0)
        product.stock = int(request.form.get('stock', product.stock))
        product.rating_avg = float(request.form.get('rating_avg', product.rating_avg) or 0)
        product.rating_count = int(request.form.get('rating_count', product.rating_count) or 0)
        product.unit = request.form.get('unit', product.unit)
        product.is_veg = request.form.get('is_veg') == 'true'
        product.is_featured = bool(request.form.get('is_featured'))
        product.is_trending = bool(request.form.get('is_trending'))
        product.is_offer = bool(request.form.get('is_offer'))
        product.is_active = bool(request.form.get('is_active'))
        product.tags = request.form.get('tags', product.tags)
        product.nutrition_info = request.form.get('nutrition_info', product.nutrition_info)

        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_path = os.path.join(current_app.root_path, 'static/images/products', filename)
                file.save(upload_path)
                product.image = filename

        db.session.commit()
        flash(f'Product "{product.name}" updated!', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/product_form.html', product=product, categories=categories)


@admin_bp.route('/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    product.is_active = False  # Soft delete
    db.session.commit()
    flash(f'Product "{product.name}" deactivated.', 'info')
    return redirect(url_for('admin.products'))


@admin_bp.route('/products/bulk-upload', methods=['POST'])
@admin_required
def bulk_upload():
    if 'csv_file' not in request.files:
        flash('No CSV file uploaded.', 'danger')
        return redirect(url_for('admin.products'))
    file = request.files['csv_file']
    if not file.filename.endswith('.csv'):
        flash('Please upload a CSV file.', 'danger')
        return redirect(url_for('admin.products'))
    stream = io.StringIO(file.stream.read().decode('UTF-8'), newline=None)
    csv_input = csv.DictReader(stream)
    count = 0
    for row in csv_input:
        slug = row.get('name', '').lower().replace(' ', '-')
        if Product.query.filter_by(slug=slug).first():
            continue
        cat = Category.query.filter_by(name=row.get('category', '')).first()
        if not cat:
            continue
        p = Product(
            name=row.get('name', ''),
            slug=slug,
            description=row.get('description', ''),
            category_id=cat.id,
            brand=row.get('brand', ''),
            price=float(row.get('price', 0)),
            stock=int(row.get('stock', 0)),
            unit=row.get('unit', 'piece'),
            is_veg=row.get('is_veg', 'true').lower() == 'true',
        )
        db.session.add(p)
        count += 1
    db.session.commit()
    flash(f'{count} products imported successfully!', 'success')
    return redirect(url_for('admin.products'))


@admin_bp.route('/orders')
@admin_required
def orders():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    query = Order.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    orders = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/orders.html', orders=orders, status_filter=status_filter)


@admin_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    message = request.form.get('message', '')
    valid_statuses = ['placed', 'confirmed', 'packed', 'out_for_delivery', 'delivered', 'cancelled', 'refunded']
    if new_status in valid_statuses:
        order.status = new_status
        if new_status == 'delivered':
            order.delivered_at = datetime.utcnow()
            order.payment_status = 'paid'
        history = OrderStatusHistory(order_id=order.id, status=new_status, message=message)
        db.session.add(history)
        db.session.commit()
        flash(f'Order #{order.order_number} updated to {new_status}.', 'success')
    return redirect(url_for('admin.orders'))


@admin_bp.route('/customers')
@admin_required
def customers():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '')
    query = User.query.filter_by(is_admin=False)
    if search:
        query = query.filter(
            (User.name.ilike(f'%{search}%')) | (User.email.ilike(f'%{search}%'))
        )
    customers = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/customers.html', customers=customers, search=search)


@admin_bp.route('/customers/<int:user_id>/toggle', methods=['POST'])
@admin_required
def toggle_customer(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    status = 'activated' if user.is_active else 'blocked'
    flash(f'Customer {user.name} has been {status}.', 'info')
    return redirect(url_for('admin.customers'))


@admin_bp.route('/coupons', methods=['GET'])
@admin_required
def coupons():
    coupons = Coupon.query.order_by(Coupon.created_at.desc() if hasattr(Coupon, 'created_at') else Coupon.id.desc()).all()
    return render_template('admin/coupons.html', coupons=coupons)


@admin_bp.route('/coupons/add', methods=['POST'])
@admin_required
def add_coupon():
    code = request.form.get('code', '').strip().upper()
    if Coupon.query.filter_by(code=code).first():
        flash('Coupon code already exists.', 'danger')
        return redirect(url_for('admin.coupons'))
    coupon = Coupon(
        code=code,
        description=request.form.get('description', ''),
        discount_type=request.form.get('discount_type', 'percent'),
        discount_value=float(request.form.get('discount_value', 0)),
        min_order_amount=float(request.form.get('min_order_amount', 0)),
        max_discount_amount=float(request.form.get('max_discount_amount', 0)) or None,
        usage_limit=int(request.form.get('usage_limit', 0)) or None,
    )
    db.session.add(coupon)
    db.session.commit()
    flash(f'Coupon {code} created!', 'success')
    return redirect(url_for('admin.coupons'))


@admin_bp.route('/coupons/delete/<int:coupon_id>', methods=['POST'])
@admin_required
def delete_coupon(coupon_id):
    coupon = Coupon.query.get_or_404(coupon_id)
    db.session.delete(coupon)
    db.session.commit()
    flash('Coupon deleted.', 'info')
    return redirect(url_for('admin.coupons'))


@admin_bp.route('/categories', methods=['GET', 'POST'])
@admin_required
def categories():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            name = request.form.get('name', '').strip()
            slug = name.lower().replace(' ', '-')
            if not Category.query.filter_by(slug=slug).first():
                cat = Category(
                    name=name,
                    slug=slug,
                    description=request.form.get('description', ''),
                    icon=request.form.get('icon', ''),
                    color=request.form.get('color', '#4CAF50'),
                )
                db.session.add(cat)
                db.session.commit()
                flash(f'Category "{name}" added!', 'success')
            else:
                flash('Category already exists.', 'danger')
        elif action == 'delete':
            cat_id = int(request.form.get('category_id', 0))
            cat = Category.query.get(cat_id)
            if cat and cat.products.count() == 0:
                db.session.delete(cat)
                db.session.commit()
                flash('Category deleted.', 'info')
            else:
                flash('Cannot delete category with products.', 'danger')
        return redirect(url_for('admin.categories'))
    categories = Category.query.order_by(Category.display_order).all()
    return render_template('admin/categories.html', categories=categories)


@admin_bp.route('/inventory')
@admin_required
def inventory():
    low_stock_products = Product.query.filter(
        Product.stock <= Product.min_stock_alert,
        Product.is_active == True
    ).all()
    out_of_stock = Product.query.filter_by(stock=0, is_active=True).all()
    return render_template('admin/inventory.html',
                           low_stock_products=low_stock_products,
                           out_of_stock=out_of_stock)
