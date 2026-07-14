# FreshMart 🛒

> **AI-Powered Grocery E-Commerce Store** built with Python Flask + IBM Watsonx.ai Granite models

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-green)](https://flask.palletsprojects.com)
[![IBM Watsonx](https://img.shields.io/badge/IBM-Watsonx.ai-0f62fe)](https://www.ibm.com/watsonx)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple)](https://getbootstrap.com)

---

## ✨ Features

### Customer Features
- 🏠 **Homepage** — Hero banner carousel, category tiles, trending & offer products
- 🔍 **Product Listing** — Search, filters (category, price, brand, rating, veg/non-veg), sorting
- 📦 **Product Detail** — Images, description, nutrition info, reviews & ratings
- 🛒 **Shopping Cart** — Quantity update, coupon/promo code, price breakdown
- ❤️ **Wishlist** / Save for Later
- 💳 **Checkout** — Address management, delivery slot, payment method (COD/UPI/Card)
- 📍 **Order Tracking** — Placed → Packed → Out for Delivery → Delivered
- 📋 **Order History** — Reorder with one click
- 🔐 **Authentication** — Signup/Login, password reset with OTP
- 👤 **User Profile** — Saved addresses, order history, preferences
- 🤖 **AI Shopping Assistant** — IBM Watsonx.ai Granite-powered chat for recipe suggestions, substitutions, diet recommendations

### Admin Features
- 📊 **Dashboard** — Revenue charts, top products, low-stock alerts
- 📦 **Product Management** — Add/Edit/Delete, bulk CSV upload, image upload
- 📋 **Order Management** — View/update status, cancel/refund
- 👥 **Customer Management** — View, block/unblock
- 🏷️ **Coupon Management** — Create, manage discount codes
- 📁 **Category Management** — Add/delete categories
- 📉 **Inventory Alerts** — Low stock & out-of-stock notifications

---

## 🗂️ Project Structure

```
grocery_store/
├── app/
│   ├── __init__.py              # App factory
│   ├── config.py                # Configuration classes
│   ├── models.py                # SQLAlchemy models
│   ├── extensions.py            # Flask extensions
│   ├── agent_instructions.py    # AI assistant configuration
│   ├── blueprints/
│   │   ├── main.py              # Homepage route
│   │   ├── auth/                # Login, signup, profile
│   │   ├── products/            # Product listing & detail
│   │   ├── cart/                # Cart management
│   │   ├── orders/              # Checkout, tracking, history
│   │   ├── wishlist/            # Wishlist
│   │   ├── admin/               # Admin panel
│   │   └── ai_assistant/        # Watsonx.ai chat
│   ├── templates/               # Jinja2 HTML templates
│   └── static/
│       ├── css/style.css        # Custom styles + dark mode
│       ├── js/main.js           # Interactions, AI chat, cart
│       └── images/              # Product & banner images
├── run.py                       # App entry point
├── seed.py                      # Database seeder
├── requirements.txt
├── .env.example                 # Environment template
└── README.md
```

---

## ⚡ Quick Start (Local Setup)

### Prerequisites
- Python 3.10+
- pip

### 1. Clone / enter the project
```bash
cd grocery_store
```

### 2. Create & activate virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
# Open .env and fill in your IBM Cloud API key and other settings
```

### 5. Seed the database
```bash
python seed.py
```

### 6. Run the development server
```bash
python run.py
```

Open your browser at: **http://localhost:5000**

**Demo credentials:**
- Customer: `priya@freshmart.com` / `Priya@123`
- Admin: `admin@freshmart.com` / `Admin@123`

---

## 🤖 IBM Watsonx.ai Setup

1. Sign up / log in at [IBM Cloud](https://cloud.ibm.com)
2. Create a **Watsonx.ai** service instance
3. Get your **API Key** from IBM Cloud → Manage → Access (IAM) → API Keys
4. Get your **Project ID** from Watsonx.ai → Projects → your project → Settings
5. Add to your `.env`:
   ```env
   IBM_CLOUD_API_KEY=your-actual-api-key
   IBM_WATSONX_PROJECT_ID=your-project-id
   IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
   WATSONX_MODEL_ID=ibm/granite-3-8b-instruct
   ```

> 💡 **Without an IBM API key**, the AI assistant uses an intelligent rule-based fallback — perfect for demo purposes.

---

## 🎨 Customizing the AI Assistant

Edit [`app/agent_instructions.py`](app/agent_instructions.py) to customize:

```python
AGENT_CONFIG = {
    "tone": "friendly",           # friendly, formal, concise
    "persona": "...",             # Describe the assistant's personality
    "default_language": "English",
    "dietary_filters": {...},     # Veg/Non-veg/Jain/Vegan rules
    "recommendation_rules": {...}, # Upsell/cross-sell logic
    "safety_rules": {...},         # Age restrictions, allergen warnings
    "quick_replies": [...],        # Chat widget quick reply chips
    "model_params": {...},         # Granite model parameters
}
```

---

## 🌐 REST API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Homepage |
| GET | `/products/` | Product listing with filters |
| GET | `/products/<slug>` | Product detail |
| GET | `/products/api/search?q=` | Live search autocomplete |
| POST | `/cart/add` | Add to cart `{product_id, quantity}` |
| POST | `/cart/update` | Update quantity `{item_id, quantity}` |
| POST | `/cart/remove` | Remove item `{item_id}` |
| POST | `/cart/apply-coupon` | Apply coupon `{code}` |
| POST | `/wishlist/toggle` | Toggle wishlist `{product_id}` |
| POST | `/orders/checkout` | Place order |
| GET | `/orders/track/<order_number>` | Track order |
| POST | `/ai/chat` | AI assistant `{message, history}` |
| POST | `/auth/login` | Login |
| POST | `/auth/signup` | Register |
| GET | `/admin/` | Admin dashboard |

---

### Production Environment Variables
```env
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=<random-256-bit-key>
JWT_SECRET_KEY=<random-256-bit-key>
DATABASE_URL=postgresql://user:pass@host:5432/freshmart
IBM_CLOUD_API_KEY=<your-key>
IBM_WATSONX_PROJECT_ID=<your-project-id>
```

> 🔐 **Never commit your `.env` file!** It's in `.gitignore` by default.

---

## 📦 Sample Data

The seed script creates:
- **12 categories** (Fruits, Dairy, Staples, Spices, etc.)
- **30+ products** with realistic Indian grocery data and nutrition info
- **4 discount coupons**: `FRESH10`, `WELCOME50`, `SAVE20`, `FREEDEL`
- **3 hero banners**
- **1 admin user** + **1 demo customer**

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, Flask 3.0, SQLAlchemy |
| AI | IBM Watsonx.ai, Granite 3.8B Instruct |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Frontend | Bootstrap 5.3, Bootstrap Icons, AOS |
| Auth | Flask-Login, Flask-JWT-Extended |
| Charts | Chart.js (admin dashboard) |
| Deployment | Gunicorn, Render / IBM Code Engine |

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit: `git commit -m "Add my feature"`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

*Built with ❤️ using IBM Watsonx.ai + Flask*
