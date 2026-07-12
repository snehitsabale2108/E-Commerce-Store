from flask import jsonify, request, render_template
from flask_login import login_required, current_user
from ...extensions import db
from ...models import WishlistItem, CartItem, Product
from . import wishlist_bp


@wishlist_bp.route('/')
@login_required
def view_wishlist():
    from flask import render_template
    items = WishlistItem.query.filter_by(user_id=current_user.id).all()
    return render_template('cart/wishlist.html', items=items)


@wishlist_bp.route('/toggle', methods=['POST'])
@login_required
def toggle():
    data = request.get_json() or request.form
    product_id = int(data.get('product_id', 0))

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404

    existing = WishlistItem.query.filter_by(
        user_id=current_user.id, product_id=product_id
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        action = 'removed'
        message = 'Removed from wishlist'
    else:
        item = WishlistItem(user_id=current_user.id, product_id=product_id)
        db.session.add(item)
        db.session.commit()
        action = 'added'
        message = 'Added to wishlist ❤️'

    count = WishlistItem.query.filter_by(user_id=current_user.id).count()
    return jsonify({'success': True, 'action': action, 'message': message, 'count': count})


@wishlist_bp.route('/remove', methods=['POST'])
@login_required
def remove():
    data = request.get_json() or request.form
    product_id = int(data.get('product_id', 0))
    item = WishlistItem.query.filter_by(
        user_id=current_user.id, product_id=product_id
    ).first()
    if item:
        db.session.delete(item)
        db.session.commit()
    return jsonify({'success': True})
