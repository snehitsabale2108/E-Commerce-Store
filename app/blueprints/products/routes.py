from flask import render_template, request, jsonify, redirect, url_for, flash
from ...models import Product, Category
from ...extensions import db
from sqlalchemy import or_
from . import products_bp


@products_bp.route('/')
def listing():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    category_slug = request.args.get('category', '')
    search_query = request.args.get('q', '').strip()
    sort_by = request.args.get('sort', 'popular')
    min_price = request.args.get('min_price', 0, type=float)
    max_price = request.args.get('max_price', 10000, type=float)
    brand_filter = request.args.get('brand', '')
    is_veg = request.args.get('veg', '')
    min_rating = request.args.get('rating', 0, type=float)

    query = Product.query.filter_by(is_active=True)

    if category_slug:
        cat = Category.query.filter_by(slug=category_slug).first()
        if cat:
            query = query.filter_by(category_id=cat.id)

    if search_query:
        query = query.filter(
            or_(
                Product.name.ilike(f'%{search_query}%'),
                Product.description.ilike(f'%{search_query}%'),
                Product.brand.ilike(f'%{search_query}%'),
                Product.tags.ilike(f'%{search_query}%')
            )
        )

    if min_price > 0:
        query = query.filter(Product.price >= min_price)
    if max_price < 10000:
        query = query.filter(Product.price <= max_price)
    if brand_filter:
        query = query.filter_by(brand=brand_filter)
    if is_veg == 'true':
        query = query.filter_by(is_veg=True)
    elif is_veg == 'false':
        query = query.filter_by(is_veg=False)
    if min_rating > 0:
        query = query.filter(Product.rating_avg >= min_rating)

    if sort_by == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort_by == 'rating':
        query = query.order_by(Product.rating_avg.desc())
    elif sort_by == 'newest':
        query = query.order_by(Product.created_at.desc())
    elif sort_by == 'discount':
        query = query.order_by(Product.discount_percent.desc())
    else:
        query = query.order_by(Product.rating_count.desc())

    products = query.paginate(page=page, per_page=per_page, error_out=False)
    categories = Category.query.filter_by(is_active=True).order_by(Category.display_order).all()

    # Get distinct brands for filter
    brands = db.session.query(Product.brand).filter(
        Product.brand.isnot(None), Product.is_active == True
    ).distinct().limit(30).all()
    brands = [b[0] for b in brands if b[0]]

    selected_category = Category.query.filter_by(slug=category_slug).first() if category_slug else None

    return render_template('products/listing.html',
                           products=products,
                           categories=categories,
                           brands=brands,
                           selected_category=selected_category,
                           search_query=search_query,
                           sort_by=sort_by,
                           category_slug=category_slug)


@products_bp.route('/<slug>')
def detail(slug):
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    related = Product.query.filter_by(
        category_id=product.category_id, is_active=True
    ).filter(Product.id != product.id).limit(6).all()
    reviews = product.reviews.order_by('created_at').all()

    import json
    nutrition = {}
    if product.nutrition_info:
        try:
            nutrition = json.loads(product.nutrition_info)
        except Exception:
            pass

    return render_template('products/detail.html',
                           product=product,
                           related=related,
                           reviews=reviews,
                           nutrition=nutrition)


@products_bp.route('/api/search')
def api_search():
    q = request.args.get('q', '').strip()
    if not q or len(q) < 2:
        return jsonify([])
    results = Product.query.filter(
        Product.name.ilike(f'%{q}%'),
        Product.is_active == True
    ).limit(8).all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'slug': p.slug,
        'price': p.effective_price,
        'image': p.image,
        'unit': p.unit,
    } for p in results])
