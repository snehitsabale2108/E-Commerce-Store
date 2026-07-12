from flask import render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from ...extensions import db
from ...models import CartItem, Product, Coupon
from . import cart_bp


@cart_bp.route('/')
@login_required
def view_cart():
    cart_items = CartItem.query.filter_by(
        user_id=current_user.id, saved_for_later=False
    ).all()
    saved_items = CartItem.query.filter_by(
        user_id=current_user.id, saved_for_later=True
    ).all()

    subtotal = sum(item.subtotal for item in cart_items)
    tax_rate = current_app.config['TAX_RATE']
    tax = round(subtotal * tax_rate, 2)
    delivery_fee = current_app.config['DELIVERY_FEE']
    free_threshold = current_app.config['FREE_DELIVERY_THRESHOLD']
    if subtotal >= free_threshold:
        delivery_fee = 0
    total = round(subtotal + tax + delivery_fee, 2)

    return render_template('cart/cart.html',
                           cart_items=cart_items,
                           saved_items=saved_items,
                           subtotal=subtotal,
                           tax=tax,
                           delivery_fee=delivery_fee,
                           free_threshold=free_threshold,
                           total=total)


@cart_bp.route('/add', methods=['POST'])
@login_required
def add_to_cart():
    data = request.get_json() or request.form
    product_id = int(data.get('product_id', 0))
    quantity = int(data.get('quantity', 1))

    product = Product.query.get(product_id)
    if not product or not product.is_active:
        return jsonify({'success': False, 'message': 'Product not found'}), 404
    if product.stock < quantity:
        return jsonify({'success': False, 'message': 'Insufficient stock'}), 400

    existing = CartItem.query.filter_by(
        user_id=current_user.id,
        product_id=product_id,
        saved_for_later=False
    ).first()

    if existing:
        existing.quantity = min(existing.quantity + quantity, product.stock)
    else:
        item = CartItem(user_id=current_user.id, product_id=product_id, quantity=quantity)
        db.session.add(item)

    db.session.commit()
    cart_count = CartItem.query.filter_by(user_id=current_user.id, saved_for_later=False).count()
    return jsonify({'success': True, 'message': 'Added to cart!', 'cart_count': cart_count})


@cart_bp.route('/update', methods=['POST'])
@login_required
def update_cart():
    data = request.get_json() or request.form
    item_id = int(data.get('item_id', 0))
    quantity = int(data.get('quantity', 1))

    item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first()
    if not item:
        return jsonify({'success': False, 'message': 'Item not found'}), 404
    if quantity <= 0:
        db.session.delete(item)
    else:
        item.quantity = min(quantity, item.product.stock)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Cart updated'})


@cart_bp.route('/remove', methods=['POST'])
@login_required
def remove_from_cart():
    data = request.get_json() or request.form
    item_id = int(data.get('item_id', 0))
    item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
    cart_count = CartItem.query.filter_by(user_id=current_user.id, saved_for_later=False).count()
    return jsonify({'success': True, 'cart_count': cart_count})


@cart_bp.route('/save-for-later', methods=['POST'])
@login_required
def save_for_later():
    data = request.get_json() or request.form
    item_id = int(data.get('item_id', 0))
    item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first()
    if item:
        item.saved_for_later = True
        db.session.commit()
        return jsonify({'success': True, 'message': 'Saved for later'})
    return jsonify({'success': False}), 404


@cart_bp.route('/move-to-cart', methods=['POST'])
@login_required
def move_to_cart():
    data = request.get_json() or request.form
    item_id = int(data.get('item_id', 0))
    item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first()
    if item:
        item.saved_for_later = False
        db.session.commit()
        return jsonify({'success': True, 'message': 'Moved to cart'})
    return jsonify({'success': False}), 404


@cart_bp.route('/apply-coupon', methods=['POST'])
@login_required
def apply_coupon():
    data = request.get_json() or request.form
    code = str(data.get('code', '')).strip().upper()

    coupon = Coupon.query.filter_by(code=code).first()
    if not coupon:
        return jsonify({'success': False, 'message': 'Invalid coupon code'})

    cart_items = CartItem.query.filter_by(user_id=current_user.id, saved_for_later=False).all()
    subtotal = sum(item.subtotal for item in cart_items)

    valid, msg = coupon.is_valid(subtotal)
    if not valid:
        return jsonify({'success': False, 'message': msg})

    discount = coupon.calculate_discount(subtotal)
    return jsonify({
        'success': True,
        'message': f'Coupon applied! You save ₹{discount:.2f}',
        'discount': discount,
        'coupon_code': code
    })
