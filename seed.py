"""
FreshMart - Database seed script.
Run: python seed.py
Populates the database with sample categories, products, coupons, and an admin user.
"""
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.extensions import db
from app.models import User, Category, Product, Coupon, Banner

app = create_app('development')


def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("[OK] Database tables created.")

        # ── Admin User ──────────────────────────────────────────
        admin = User(
            name='Admin',
            email=app.config['ADMIN_EMAIL'],
            is_admin=True,
            is_verified=True,
            is_active=True,
        )
        admin.set_password(app.config['ADMIN_PASSWORD'])
        db.session.add(admin)

        # Demo user
        demo = User(
            name='Priya Sharma',
            email='priya@example.com',
            phone='9876543210',
            is_verified=True,
            diet_preference='veg',
        )
        demo.set_password('demo1234')
        db.session.add(demo)
        db.session.flush()
        print("[OK] Users created.")

        # ── Categories ──────────────────────────────────────────
        categories_data = [
            {'name': 'Fruits & Vegetables', 'slug': 'fruits-vegetables', 'icon': '🥦', 'color': '#2e7d32', 'order': 1},
            {'name': 'Dairy & Eggs', 'slug': 'dairy-eggs', 'icon': '🥛', 'color': '#1565c0', 'order': 2},
            {'name': 'Staples & Grains', 'slug': 'staples-grains', 'icon': '🌾', 'color': '#f57f17', 'order': 3},
            {'name': 'Spices & Masala', 'slug': 'spices-masala', 'icon': '🌶️', 'color': '#b71c1c', 'order': 4},
            {'name': 'Oils & Ghee', 'slug': 'oils-ghee', 'icon': '🫒', 'color': '#e65100', 'order': 5},
            {'name': 'Snacks & Namkeen', 'slug': 'snacks-namkeen', 'icon': '🥜', 'color': '#6a1b9a', 'order': 6},
            {'name': 'Beverages', 'slug': 'beverages', 'icon': '☕', 'color': '#4e342e', 'order': 7},
            {'name': 'Personal Care', 'slug': 'personal-care', 'icon': '🧴', 'color': '#00695c', 'order': 8},
            {'name': 'Household', 'slug': 'household', 'icon': '🧹', 'color': '#37474f', 'order': 9},
            {'name': 'Bakery & Breads', 'slug': 'bakery-breads', 'icon': '🍞', 'color': '#8d6e63', 'order': 10},
            {'name': 'Meat & Seafood', 'slug': 'meat-seafood', 'icon': '🍗', 'color': '#c62828', 'order': 11},
            {'name': 'Frozen Foods', 'slug': 'frozen-foods', 'icon': '🧊', 'color': '#0277bd', 'order': 12},
        ]
        cats = {}
        for c in categories_data:
            cat = Category(
                name=c['name'], slug=c['slug'], icon=c['icon'],
                color=c['color'], display_order=c['order'], is_active=True
            )
            db.session.add(cat)
            db.session.flush()
            cats[c['slug']] = cat
        print("[OK] Categories created.")

        # ── Products ───────────────────────────────────────────
        products_data = [
            # Fruits & Vegetables
            {'name': 'Fresh Spinach (Palak)', 'slug': 'fresh-spinach-palak', 'cat': 'fruits-vegetables', 'brand': 'FreshMart Farms', 'price': 25, 'mrp': 30, 'stock': 150, 'unit': '250g', 'is_veg': True, 'is_featured': True, 'rating': 4.5, 'reviews': 128,
             'nutrition': {'calories': '23 kcal', 'protein': '2.9g', 'carbs': '3.6g', 'fiber': '2.2g', 'fat': '0.4g'},
             'tags': 'green leafy vegetables healthy iron'},
            {'name': 'Organic Tomatoes', 'slug': 'organic-tomatoes', 'cat': 'fruits-vegetables', 'brand': 'Green Farms', 'price': 35, 'mrp': 40, 'stock': 200, 'unit': '500g', 'is_veg': True, 'is_trending': True, 'rating': 4.3, 'reviews': 95,
             'nutrition': {'calories': '18 kcal', 'protein': '0.9g', 'carbs': '3.9g', 'fiber': '1.2g', 'fat': '0.2g'},
             'tags': 'tomatoes organic fresh vegetables'},
            {'name': 'Royal Gala Apples', 'slug': 'royal-gala-apples', 'cat': 'fruits-vegetables', 'brand': 'Himalayan Fresh', 'price': 149, 'mrp': 180, 'stock': 80, 'unit': '1kg', 'is_veg': True, 'is_featured': True, 'is_offer': True, 'rating': 4.7, 'reviews': 342,
             'nutrition': {'calories': '52 kcal', 'protein': '0.3g', 'carbs': '14g', 'fiber': '2.4g', 'fat': '0.2g'},
             'tags': 'apples fruit fresh imported'},
            {'name': 'Alphonso Mangoes', 'slug': 'alphonso-mangoes', 'cat': 'fruits-vegetables', 'brand': 'Devgad Farms', 'price': 399, 'mrp': 450, 'stock': 30, 'unit': '1kg (6 pcs)', 'is_veg': True, 'is_trending': True, 'is_featured': True, 'rating': 4.9, 'reviews': 567,
             'nutrition': {'calories': '60 kcal', 'protein': '0.8g', 'carbs': '15g', 'fiber': '1.6g', 'fat': '0.4g'},
             'tags': 'mango alphonso hapus seasonal fruit summer'},
            {'name': 'Baby Potatoes', 'slug': 'baby-potatoes', 'cat': 'fruits-vegetables', 'brand': 'FreshMart', 'price': 45, 'mrp': 55, 'stock': 180, 'unit': '1kg', 'is_veg': True, 'rating': 4.2, 'reviews': 76,
             'nutrition': {'calories': '77 kcal', 'protein': '2g', 'carbs': '17g', 'fiber': '2.2g', 'fat': '0.1g'},
             'tags': 'potato vegetables baby aloo'},
            {'name': 'Green Capsicum', 'slug': 'green-capsicum', 'cat': 'fruits-vegetables', 'brand': 'FreshMart', 'price': 30, 'mrp': 40, 'stock': 120, 'unit': '250g', 'is_veg': True, 'rating': 4.0, 'reviews': 43,
             'nutrition': {'calories': '31 kcal', 'protein': '1g', 'carbs': '6g', 'fiber': '2.1g', 'fat': '0.3g'},
             'tags': 'capsicum shimla mirch bell pepper vegetables'},

            # Dairy & Eggs
            {'name': 'Amul Gold Full Cream Milk', 'slug': 'amul-gold-full-cream-milk', 'cat': 'dairy-eggs', 'brand': 'Amul', 'price': 31, 'mrp': 31, 'stock': 500, 'unit': '500ml', 'is_veg': True, 'is_featured': True, 'is_trending': True, 'rating': 4.6, 'reviews': 1243,
             'nutrition': {'calories': '62 kcal', 'protein': '3.2g', 'fat': '3.5g', 'carbs': '4.8g', 'calcium': '120mg'},
             'tags': 'milk dairy amul full cream'},
            {'name': 'Amul Butter (Salted)', 'slug': 'amul-butter-salted', 'cat': 'dairy-eggs', 'brand': 'Amul', 'price': 55, 'mrp': 55, 'stock': 300, 'unit': '100g', 'is_veg': True, 'is_featured': True, 'rating': 4.8, 'reviews': 892,
             'nutrition': {'calories': '717 kcal', 'fat': '81g', 'protein': '0.9g', 'carbs': '0.1g'},
             'tags': 'butter amul dairy salted'},
            {'name': 'Mother Dairy Paneer', 'slug': 'mother-dairy-paneer', 'cat': 'dairy-eggs', 'brand': 'Mother Dairy', 'price': 89, 'mrp': 95, 'stock': 200, 'unit': '200g', 'is_veg': True, 'is_trending': True, 'rating': 4.5, 'reviews': 445,
             'nutrition': {'calories': '265 kcal', 'protein': '18g', 'fat': '20g', 'carbs': '3.4g', 'calcium': '480mg'},
             'tags': 'paneer cottage cheese dairy fresh'},
            {'name': 'Farm Fresh Eggs', 'slug': 'farm-fresh-eggs', 'cat': 'dairy-eggs', 'brand': 'Keggfarms', 'price': 84, 'mrp': 90, 'stock': 400, 'unit': '12 pcs', 'is_veg': False, 'is_featured': True, 'rating': 4.4, 'reviews': 312,
             'nutrition': {'calories': '155 kcal', 'protein': '13g', 'fat': '11g', 'carbs': '1.1g'},
             'tags': 'eggs fresh farm protein'},
            {'name': 'Nestle A+ Dahi', 'slug': 'nestle-a-plus-dahi', 'cat': 'dairy-eggs', 'brand': 'Nestle', 'price': 40, 'mrp': 45, 'stock': 250, 'unit': '400g', 'is_veg': True, 'rating': 4.3, 'reviews': 189,
             'nutrition': {'calories': '60 kcal', 'protein': '3.5g', 'fat': '3.3g', 'carbs': '4.5g'},
             'tags': 'dahi yogurt curd dairy nestle'},

            # Staples & Grains
            {'name': 'India Gate Basmati Rice', 'slug': 'india-gate-basmati-rice', 'cat': 'staples-grains', 'brand': 'India Gate', 'price': 299, 'mrp': 350, 'stock': 120, 'unit': '5kg', 'is_veg': True, 'is_featured': True, 'is_offer': True, 'rating': 4.7, 'reviews': 2341,
             'nutrition': {'calories': '365 kcal', 'protein': '7g', 'carbs': '80g', 'fat': '0.7g', 'fiber': '0.4g'},
             'tags': 'basmati rice india gate premium long grain'},
            {'name': 'Aashirvaad Atta', 'slug': 'aashirvaad-atta', 'cat': 'staples-grains', 'brand': 'Aashirvaad', 'price': 280, 'mrp': 320, 'stock': 200, 'unit': '10kg', 'is_veg': True, 'is_featured': True, 'is_trending': True, 'rating': 4.6, 'reviews': 1876,
             'nutrition': {'calories': '340 kcal', 'protein': '11g', 'carbs': '72g', 'fat': '1.7g', 'fiber': '3g'},
             'tags': 'atta wheat flour chapati roti aashirvaad'},
            {'name': 'Tata Sampann Toor Dal', 'slug': 'tata-sampann-toor-dal', 'cat': 'staples-grains', 'brand': 'Tata Sampann', 'price': 165, 'mrp': 185, 'stock': 180, 'unit': '1kg', 'is_veg': True, 'is_featured': True, 'rating': 4.5, 'reviews': 432,
             'nutrition': {'calories': '343 kcal', 'protein': '22g', 'carbs': '60g', 'fat': '1.7g', 'fiber': '15g'},
             'tags': 'toor dal arhar dal tata sampann lentil protein'},
            {'name': 'Quaker Oats', 'slug': 'quaker-oats', 'cat': 'staples-grains', 'brand': 'Quaker', 'price': 135, 'mrp': 150, 'stock': 250, 'unit': '1kg', 'is_veg': True, 'is_trending': True, 'rating': 4.4, 'reviews': 567,
             'nutrition': {'calories': '375 kcal', 'protein': '13g', 'carbs': '67g', 'fat': '6.9g', 'fiber': '10g'},
             'tags': 'oats quaker breakfast healthy fiber'},
            {'name': 'Rajdhani Chana Dal', 'slug': 'rajdhani-chana-dal', 'cat': 'staples-grains', 'brand': 'Rajdhani', 'price': 95, 'mrp': 110, 'stock': 140, 'unit': '1kg', 'is_veg': True, 'rating': 4.3, 'reviews': 234,
             'nutrition': {'calories': '364 kcal', 'protein': '20g', 'carbs': '61g', 'fat': '5g', 'fiber': '18g'},
             'tags': 'chana dal chickpea lentil rajdhani protein'},

            # Spices & Masala
            {'name': 'MDH Chhole Masala', 'slug': 'mdh-chhole-masala', 'cat': 'spices-masala', 'brand': 'MDH', 'price': 55, 'mrp': 60, 'stock': 300, 'unit': '100g', 'is_veg': True, 'is_featured': True, 'rating': 4.6, 'reviews': 892,
             'nutrition': {'calories': '299 kcal', 'protein': '12g', 'carbs': '49g', 'fat': '9g', 'fiber': '22g'},
             'tags': 'masala mdh spice chhole chole'},
            {'name': 'Everest Garam Masala', 'slug': 'everest-garam-masala', 'cat': 'spices-masala', 'brand': 'Everest', 'price': 75, 'mrp': 85, 'stock': 250, 'unit': '100g', 'is_veg': True, 'is_trending': True, 'rating': 4.7, 'reviews': 1234,
             'nutrition': {'calories': '317 kcal', 'protein': '11g', 'carbs': '53g', 'fat': '10g'},
             'tags': 'garam masala everest spice blend'},
            {'name': 'Kashmiri Red Chilli Powder', 'slug': 'kashmiri-red-chilli-powder', 'cat': 'spices-masala', 'brand': 'MDH', 'price': 45, 'mrp': 55, 'stock': 200, 'unit': '100g', 'is_veg': True, 'is_offer': True, 'rating': 4.5, 'reviews': 456,
             'nutrition': {'calories': '325 kcal', 'fat': '12g', 'carbs': '55g', 'fiber': '27g'},
             'tags': 'chilli red kashmiri powder spice colour'},
            {'name': 'Organic Turmeric Powder', 'slug': 'organic-turmeric-powder', 'cat': 'spices-masala', 'brand': '24 Mantra', 'price': 85, 'mrp': 100, 'stock': 150, 'unit': '200g', 'is_veg': True, 'rating': 4.8, 'reviews': 678,
             'nutrition': {'calories': '354 kcal', 'protein': '8g', 'carbs': '65g', 'fat': '10g', 'fiber': '21g'},
             'tags': 'turmeric haldi organic spice 24 mantra'},

            # Oils & Ghee
            {'name': 'Amul Pure Ghee', 'slug': 'amul-pure-ghee', 'cat': 'oils-ghee', 'brand': 'Amul', 'price': 290, 'mrp': 310, 'stock': 200, 'unit': '500ml', 'is_veg': True, 'is_featured': True, 'is_trending': True, 'rating': 4.8, 'reviews': 2341,
             'nutrition': {'calories': '900 kcal', 'fat': '99.5g', 'saturated_fat': '66g', 'cholesterol': '256mg'},
             'tags': 'ghee amul pure desi clarified butter'},
            {'name': 'Fortune Sunflower Oil', 'slug': 'fortune-sunflower-oil', 'cat': 'oils-ghee', 'brand': 'Fortune', 'price': 195, 'mrp': 220, 'stock': 300, 'unit': '1L', 'is_veg': True, 'is_featured': True, 'is_offer': True, 'rating': 4.4, 'reviews': 876,
             'nutrition': {'calories': '900 kcal', 'fat': '100g', 'vitamin_e': '41mg'},
             'tags': 'sunflower oil fortune cooking oil refined'},
            {'name': 'Dhara Cold Pressed Mustard Oil', 'slug': 'dhara-mustard-oil', 'cat': 'oils-ghee', 'brand': 'Dhara', 'price': 165, 'mrp': 185, 'stock': 150, 'unit': '1L', 'is_veg': True, 'is_trending': True, 'rating': 4.5, 'reviews': 432,
             'nutrition': {'calories': '900 kcal', 'fat': '100g', 'omega3': '6g'},
             'tags': 'mustard oil sarson kachchi ghani cold pressed'},

            # Snacks
            {'name': 'Haldirams Aloo Bhujia', 'slug': 'haldirams-aloo-bhujia', 'cat': 'snacks-namkeen', 'brand': "Haldiram's", 'price': 30, 'mrp': 35, 'stock': 500, 'unit': '150g', 'is_veg': True, 'is_trending': True, 'rating': 4.6, 'reviews': 3421,
             'nutrition': {'calories': '536 kcal', 'fat': '30g', 'carbs': '57g', 'protein': '8g'},
             'tags': 'snack namkeen haldirams bhujia aloo'},
            {'name': 'Lay\'s Classic Salted', 'slug': 'lays-classic-salted', 'cat': 'snacks-namkeen', 'brand': 'Lay\'s', 'price': 20, 'mrp': 20, 'stock': 400, 'unit': '52g', 'is_veg': True, 'is_featured': True, 'rating': 4.3, 'reviews': 1876,
             'nutrition': {'calories': '536 kcal', 'fat': '32g', 'carbs': '53g', 'protein': '6g', 'sodium': '560mg'},
             'tags': 'chips lays crisps snack party'},
            {'name': 'Too Yumm Multigrain Chips', 'slug': 'too-yumm-multigrain', 'cat': 'snacks-namkeen', 'brand': 'Too Yumm', 'price': 20, 'mrp': 20, 'stock': 300, 'unit': '35g', 'is_veg': True, 'is_offer': True, 'rating': 4.1, 'reviews': 543,
             'nutrition': {'calories': '397 kcal', 'fat': '13g', 'carbs': '62g', 'protein': '9g', 'fiber': '8g'},
             'tags': 'multigrain chips healthy baked snack'},

            # Beverages
            {'name': 'Tata Tea Gold', 'slug': 'tata-tea-gold', 'cat': 'beverages', 'brand': 'Tata Tea', 'price': 275, 'mrp': 300, 'stock': 200, 'unit': '500g', 'is_veg': True, 'is_featured': True, 'is_trending': True, 'rating': 4.6, 'reviews': 2134,
             'nutrition': {'calories': '2 kcal per cup', 'antioxidants': 'High', 'caffeine': 'Moderate'},
             'tags': 'tea tata gold masala chai beverage'},
            {'name': 'Nescafe Classic Coffee', 'slug': 'nescafe-classic-coffee', 'cat': 'beverages', 'brand': 'Nescafe', 'price': 250, 'mrp': 275, 'stock': 150, 'unit': '100g', 'is_veg': True, 'is_trending': True, 'rating': 4.5, 'reviews': 1342,
             'nutrition': {'calories': '2 kcal per cup', 'caffeine': '57mg per cup'},
             'tags': 'coffee nescafe instant beverage morning'},
            {'name': 'Real Fruit Juice (Mixed Fruit)', 'slug': 'real-mixed-fruit-juice', 'cat': 'beverages', 'brand': 'Real', 'price': 95, 'mrp': 110, 'stock': 250, 'unit': '1L', 'is_veg': True, 'is_offer': True, 'rating': 4.2, 'reviews': 567,
             'nutrition': {'calories': '58 kcal', 'sugar': '14g', 'vitamin_c': '15% DV'},
             'tags': 'juice real fruit beverage drink mixed'},

            # Meat & Seafood
            {'name': 'Suguna Fresh Chicken (Curry Cut)', 'slug': 'suguna-chicken-curry-cut', 'cat': 'meat-seafood', 'brand': 'Suguna', 'price': 249, 'mrp': 280, 'stock': 50, 'unit': '500g', 'is_veg': False, 'is_featured': True, 'is_trending': True, 'rating': 4.5, 'reviews': 678,
             'nutrition': {'calories': '239 kcal', 'protein': '27g', 'fat': '14g', 'carbs': '0g'},
             'tags': 'chicken fresh suguna curry cut non veg protein'},
            {'name': 'Prawns (Medium)', 'slug': 'prawns-medium', 'cat': 'meat-seafood', 'brand': 'FreshMart', 'price': 399, 'mrp': 450, 'stock': 30, 'unit': '500g', 'is_veg': False, 'is_offer': True, 'rating': 4.3, 'reviews': 234,
             'nutrition': {'calories': '99 kcal', 'protein': '24g', 'fat': '0.3g', 'carbs': '0g', 'cholesterol': '189mg'},
             'tags': 'prawns shrimp seafood non veg fresh'},
        ]

        for pd in products_data:
            p = Product(
                name=pd['name'],
                slug=pd['slug'],
                description=f"Premium quality {pd['name']} - {pd.get('tags', '')}. Fresh and carefully sourced for FreshMart customers.",
                category_id=cats[pd['cat']].id,
                brand=pd.get('brand', ''),
                price=pd['price'],
                mrp=pd.get('mrp', pd['price']),
                discount_percent=round((1 - pd['price'] / pd.get('mrp', pd['price'])) * 100, 1) if pd.get('mrp') and pd.get('mrp') > pd['price'] else 0,
                stock=pd['stock'],
                unit=pd['unit'],
                is_veg=pd.get('is_veg', True),
                is_featured=pd.get('is_featured', False),
                is_trending=pd.get('is_trending', False),
                is_offer=pd.get('is_offer', False),
                is_active=True,
                tags=pd.get('tags', ''),
                rating_avg=pd.get('rating', 4.0),
                rating_count=pd.get('reviews', 0),
                nutrition_info=json.dumps(pd.get('nutrition', {})),
                image='default_product.png',
            )
            db.session.add(p)

        print(f"[OK] {len(products_data)} products created.")

        # ── Coupons ────────────────────────────────────────────
        coupons = [
            Coupon(code='FRESH10', description='10% off on first order', discount_type='percent', discount_value=10, min_order_amount=200, max_discount_amount=100, usage_limit=1000, is_active=True, valid_from=datetime.utcnow(), valid_until=datetime(2026, 12, 31)),
            Coupon(code='WELCOME50', description='Flat ₹50 off for new users', discount_type='flat', discount_value=50, min_order_amount=299, usage_limit=500, is_active=True, valid_from=datetime.utcnow(), valid_until=datetime(2026, 12, 31)),
            Coupon(code='SAVE20', description='20% off on orders above ₹999', discount_type='percent', discount_value=20, min_order_amount=999, max_discount_amount=200, usage_limit=200, is_active=True, valid_from=datetime.utcnow(), valid_until=datetime(2026, 12, 31)),
            Coupon(code='FREEDEL', description='Free delivery on any order', discount_type='flat', discount_value=49, min_order_amount=0, is_active=True, valid_from=datetime.utcnow(), valid_until=datetime(2026, 12, 31)),
        ]
        for c in coupons:
            db.session.add(c)

        # ── Banners ────────────────────────────────────────────
        banners = [
            Banner(title='Farm Fresh, Delivered Fast', subtitle='Get the freshest fruits & vegetables at your doorstep in under 2 hours', link='/products/?category=fruits-vegetables', button_text='Shop Fresh', bg_color='#1a472a', text_color='#ffffff', display_order=1, is_active=True),
            Banner(title='10% Off on Your First Order', subtitle='Use code FRESH10 at checkout. Min order ₹200', link='/products/', button_text='Order Now', bg_color='#1a237e', text_color='#ffffff', display_order=2, is_active=True),
            Banner(title='Premium Dairy Every Morning', subtitle='Amul, Mother Dairy & more. Fresh milk at your door by 7 AM', link='/products/?category=dairy-eggs', button_text='Subscribe Now', bg_color='#0d47a1', text_color='#ffffff', display_order=3, is_active=True),
        ]
        for b in banners:
            db.session.add(b)

        db.session.commit()
        print("[OK] Coupons and banners created.")
        print("\n[DONE] Database seeded successfully!")
        print(f"   Admin: {app.config['ADMIN_EMAIL']} / {app.config['ADMIN_PASSWORD']}")
        print(f"   Demo User: priya@example.com / demo1234")


if __name__ == '__main__':
    seed()
