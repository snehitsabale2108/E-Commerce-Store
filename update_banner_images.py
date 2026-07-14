"""
Safely updates the `image` field on existing Banner rows,
without touching any other data in the database.
Run with: python update_banner_images.py
"""
from app import create_app, db
from app.models import Banner

app = create_app('development')

# Map: banner title -> image filename
IMAGE_MAP = {
    'Farm Fresh, Delivered Fast': 'shop_fresh.png',
    '10% Off on Your First Order': 'order_now.png',
    'Premium Dairy Every Morning': 'subscribe_now.png',
}

with app.app_context():
    updated = 0
    for title, image in IMAGE_MAP.items():
        banner = Banner.query.filter_by(title=title).first()
        if banner:
            banner.image = image
            updated += 1
            print(f"[OK] Set image for: {title} -> {image}")
        else:
            print(f"[SKIP] No banner found with title: {title}")

    db.session.commit()
    print(f"\nDone. {updated} banner(s) updated. No other data was touched.")