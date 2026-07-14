from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user
from ..models import Product, Category, Banner

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    categories = Category.query.filter_by(is_active=True).order_by(Category.display_order).all()
    featured_products = Product.query.filter_by(is_featured=True, is_active=True).limit(12).all()
    trending_products = Product.query.filter_by(is_trending=True, is_active=True).limit(8).all()
    offer_products = Product.query.filter_by(is_offer=True, is_active=True).limit(8).all()
    banners = Banner.query.filter_by(is_active=True).order_by(Banner.display_order).limit(5).all()
    return render_template('index.html',
                           categories=categories,
                           featured_products=featured_products,
                           trending_products=trending_products,
                           offer_products=offer_products,
                           banners=banners)

@main_bp.route('/help-center')
def help_center():
    return render_template('pages/help_center.html')


@main_bp.route('/return-policy')
def return_policy():
    return render_template('pages/return_policy.html')


@main_bp.route('/contact-us', methods=['GET', 'POST'])
def contact_us():
    if request.method == 'POST':
        flash("Thanks! We've received your message and will get back to you soon.", 'success')
        return redirect(url_for('main.contact_us'))
    return render_template('pages/contact_us.html')