from flask import render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import random
import string
from ...extensions import db
from ...models import Order, OrderItem, OrderStatusHistory, CartItem, Product, Address, Coupon
from . import orders_bp


def generate_order_number():
    chars = string.ascii_uppercase + string.digits
    return 'FM' + ''.join(random.choices(chars, k=8))


@orders_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(
        user_id=current_user.id, saved_for_later=False
    ).all()
    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart.view_cart'))

    addresses = current_user.addresses.all()
    subtotal = sum(item.subtotal for item in cart_items)
    tax_rate = current_app.config['TAX_RATE']
    tax = round(subtotal * tax_rate, 2)
    delivery_fee = current_app.config['DELIVERY_FEE']
    free_threshold = current_app.config['FREE_DELIVERY_THRESHOLD']
    if subtotal >= free_threshold:
        delivery_fee = 0

    if request.method == 'POST':
        address_id = request.form.get('address_id', type=int)
        payment_method = request.form.get('payment_method', 'cod')
        delivery_slot = request.form.get('delivery_slot', 'Today 7-9 PM')
        coupon_code = request.form.get('coupon_code', '').strip().upper()
        notes = request.form.get('notes', '').strip()

        discount = 0
        if coupon_code:
            coupon = Coupon.query.filter_by(code=coupon_code).first()
            if coupon:
                valid, _ = coupon.is_valid(subtotal)
                if valid:
                    discount = coupon.calculate_discount(subtotal)
                    coupon.usage_count += 1

        total = round(subtotal + tax + delivery_fee - discount, 2)

        order = Order(
            order_number=generate_order_number(),
            user_id=current_user.id,
            address_id=address_id,
            status='placed',
            subtotal=subtotal,
            tax=tax,
            delivery_fee=delivery_fee,
            discount=discount,
            total=total,
            payment_method=payment_method,
            payment_status='paid' if payment_method != 'cod' else 'pending',
            delivery_slot=delivery_slot,
            coupon_code=coupon_code if coupon_code else None,
            notes=notes,
            estimated_delivery=datetime.utcnow() + timedelta(hours=4)
        )
        db.session.add(order)
        db.session.flush()

        for cart_item in cart_items:
            oi = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                product_name=cart_item.product.name,
                quantity=cart_item.quantity,
                unit_price=cart_item.product.effective_price,
                subtotal=cart_item.subtotal
            )
            db.session.add(oi)
            cart_item.product.stock = max(0, cart_item.product.stock - cart_item.quantity)

        history = OrderStatusHistory(
            order_id=order.id,
            status='placed',
            message='Your order has been placed successfully!'
        )
        db.session.add(history)

        CartItem.query.filter_by(user_id=current_user.id, saved_for_later=False).delete()
        db.session.commit()

        flash(f'Order {order.order_number} placed successfully! 🎉', 'success')
        return redirect(url_for('orders.track', order_number=order.order_number))

    delivery_slots = [
        'Today 7-9 PM',
        'Tomorrow 7-9 AM',
        'Tomorrow 11 AM - 1 PM',
        'Tomorrow 3-5 PM',
        'Tomorrow 7-9 PM',
    ]

    return render_template('orders/checkout.html',
                           cart_items=cart_items,
                           addresses=addresses,
                           subtotal=subtotal,
                           tax=tax,
                           delivery_fee=delivery_fee,
                           free_threshold=free_threshold,
                           delivery_slots=delivery_slots)


@orders_bp.route('/track/<order_number>')
@login_required
def track(order_number):
    order = Order.query.filter_by(
        order_number=order_number, user_id=current_user.id
    ).first_or_404()
    history = order.status_history.order_by(OrderStatusHistory.created_at).all()
    return render_template('orders/tracking.html', order=order, history=history)


@orders_bp.route('/history')
@login_required
def history():
    page = request.args.get('page', 1, type=int)
    orders = Order.query.filter_by(user_id=current_user.id).order_by(
        Order.created_at.desc()
    ).paginate(page=page, per_page=10, error_out=False)
    return render_template('orders/history.html', orders=orders)


@orders_bp.route('/reorder/<int:order_id>', methods=['POST'])
@login_required
def reorder(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    added = 0
    for item in order.items:
        product = Product.query.get(item.product_id)
        if product and product.is_active and product.stock > 0:
            existing = CartItem.query.filter_by(
                user_id=current_user.id,
                product_id=item.product_id,
                saved_for_later=False
            ).first()
            if existing:
                existing.quantity = min(existing.quantity + item.quantity, product.stock)
            else:
                ci = CartItem(
                    user_id=current_user.id,
                    product_id=item.product_id,
                    quantity=min(item.quantity, product.stock)
                )
                db.session.add(ci)
            added += 1
    db.session.commit()
    flash(f'{added} item(s) added to your cart!', 'success')
    return redirect(url_for('cart.view_cart'))


@orders_bp.route('/cancel/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    if order.status in ['placed', 'confirmed']:
        order.status = 'cancelled'
        for item in order.items:
            product = Product.query.get(item.product_id)
            if product:
                product.stock += item.quantity
        history = OrderStatusHistory(
            order_id=order.id,
            status='cancelled',
            message='Order cancelled by customer.'
        )
        db.session.add(history)
        db.session.commit()
        flash('Order cancelled successfully.', 'info')
    else:
        flash('Order cannot be cancelled at this stage.', 'warning')
    return redirect(url_for('orders.history'))


@orders_bp.route('/api/status/<order_number>')
@login_required
def api_status(order_number):
    order = Order.query.filter_by(
        order_number=order_number, user_id=current_user.id
    ).first_or_404()
    return jsonify(order.to_dict())
