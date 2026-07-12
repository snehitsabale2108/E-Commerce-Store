import os
import json
import requests
from flask import request, jsonify, current_app
from flask_login import current_user

from ...agent_instructions import AGENT_CONFIG
from . import ai_bp

# ─── IBM IAM Token Cache ───────────────────────────────────────────────────────
_token_cache = {'token': None, 'expires_at': 0}


def get_iam_token():
    """Fetch or return cached IBM Cloud IAM token."""
    import time
    if _token_cache['token'] and time.time() < _token_cache['expires_at']:
        return _token_cache['token']

    api_key = current_app.config['IBM_CLOUD_API_KEY']
    if not api_key:
        raise ValueError("IBM_CLOUD_API_KEY is not configured.")

    resp = requests.post(
        'https://iam.cloud.ibm.com/identity/token',
        data={
            'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
            'apikey': api_key
        },
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        timeout=10
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache['token'] = data['access_token']
    _token_cache['expires_at'] = time.time() + data.get('expires_in', 3600) - 60
    return _token_cache['token']


def call_watsonx(prompt: str, system_prompt: str = '') -> str:
    """Send a prompt to IBM Watsonx.ai Granite model and return the response text."""
    token = get_iam_token()
    base_url = current_app.config['IBM_WATSONX_URL']
    project_id = current_app.config['IBM_WATSONX_PROJECT_ID']
    model_id = current_app.config['WATSONX_MODEL_ID']
    params = AGENT_CONFIG['model_params']

    # Build full prompt for Granite chat
    messages = []
    if system_prompt:
        messages.append({'role': 'system', 'content': system_prompt})
    messages.append({'role': 'user', 'content': prompt})

    payload = {
        'model_id': model_id,
        'project_id': project_id,
        'messages': messages,
        'parameters': {
            'decoding_method': params.get('decoding_method', 'greedy'),
            'max_new_tokens': params.get('max_new_tokens', 512),
            'min_new_tokens': params.get('min_new_tokens', 20),
            'temperature': params.get('temperature', 0.7),
            'top_k': params.get('top_k', 50),
            'top_p': params.get('top_p', 0.9),
            'repetition_penalty': params.get('repetition_penalty', 1.1),
        }
    }

    url = f"{base_url}/ml/v1/text/chat?version=2024-05-01"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    result = resp.json()

    # Extract the generated text
    try:
        return result['choices'][0]['message']['content'].strip()
    except (KeyError, IndexError):
        return "I'm having trouble responding right now. Please try again."


def build_system_prompt(user_context: dict) -> str:
    """Build the system prompt from AGENT_CONFIG and user context."""
    config = AGENT_CONFIG
    template = config['system_prompt_template']

    diet = user_context.get('diet_preference', 'veg')
    diet_instruction = config['dietary_filters'].get(diet, '')

    return template.format(
        name=config['name'],
        role=config['role'],
        persona=config['persona'],
        diet_preference=f"{diet} - {diet_instruction}",
        location=user_context.get('location', 'India'),
        language=user_context.get('language', config['default_language']),
        cart_items=user_context.get('cart_items', 'Empty cart'),
        order_history=user_context.get('order_history', 'No previous orders'),
        user_message='{user_message}'  # placeholder, will be replaced
    ).replace('\nRespond helpfully to: {user_message}', '')


@ai_bp.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint for the AI shopping assistant."""
    data = request.get_json() or {}
    user_message = data.get('message', '').strip()
    conversation_history = data.get('history', [])

    if not user_message:
        return jsonify({'success': False, 'message': 'Please enter a message.'}), 400

    if len(user_message) > 1000:
        return jsonify({'success': False, 'message': 'Message too long.'}), 400

    # Build user context
    user_context = {
        'diet_preference': 'veg',
        'location': 'India',
        'language': 'English',
        'cart_items': 'Unknown',
        'order_history': 'Unknown'
    }

    if current_user.is_authenticated:
        user_context['diet_preference'] = current_user.diet_preference or 'veg'
        user_context['language'] = current_user.language_preference or 'English'

        from ...models import CartItem, Order
        cart_items = CartItem.query.filter_by(
            user_id=current_user.id, saved_for_later=False
        ).all()
        if cart_items:
            cart_summary = ', '.join([f"{ci.product.name} x{ci.quantity}" for ci in cart_items[:5]])
            user_context['cart_items'] = cart_summary
        else:
            user_context['cart_items'] = 'Empty cart'

        recent_order = Order.query.filter_by(user_id=current_user.id).order_by(
            Order.created_at.desc()
        ).first()
        if recent_order:
            user_context['order_history'] = f"Last order: {recent_order.order_number} ({recent_order.status})"

    system_prompt = build_system_prompt(user_context)

    # Safety filter: check for age-restricted content
    restricted_keywords = ['alcohol', 'beer', 'wine', 'whiskey', 'cigarette', 'tobacco', 'vodka', 'rum']
    message_lower = user_message.lower()
    if any(kw in message_lower for kw in restricted_keywords):
        if not current_user.is_authenticated:
            return jsonify({
                'success': True,
                'reply': "🔞 Age-restricted products require age verification. Please sign up and verify your age to access these items.",
                'quick_replies': AGENT_CONFIG['quick_replies'][:4]
            })

    # Check if IBM API key is configured
    ibm_key = current_app.config.get('IBM_CLOUD_API_KEY', '')
    if not ibm_key or ibm_key == 'your-ibm-cloud-api-key-here':
        # Fallback: intelligent rule-based responses
        reply = get_fallback_response(user_message, user_context)
        return jsonify({
            'success': True,
            'reply': reply,
            'quick_replies': AGENT_CONFIG['quick_replies'],
            'mode': 'fallback'
        })

    try:
        # Build context-aware prompt
        full_prompt = f"{system_prompt}\n\nUser: {user_message}\nFreshie:"
        reply = call_watsonx(full_prompt, system_prompt)

        return jsonify({
            'success': True,
            'reply': reply,
            'quick_replies': AGENT_CONFIG['quick_replies'],
            'mode': 'watsonx'
        })

    except requests.exceptions.ConnectionError:
        reply = get_fallback_response(user_message, user_context)
        return jsonify({'success': True, 'reply': reply, 'quick_replies': AGENT_CONFIG['quick_replies'], 'mode': 'fallback'})
    except requests.exceptions.HTTPError as e:
        current_app.logger.error(f"Watsonx API error: {e}")
        reply = get_fallback_response(user_message, user_context)
        return jsonify({'success': True, 'reply': reply, 'quick_replies': AGENT_CONFIG['quick_replies'], 'mode': 'fallback'})
    except Exception as e:
        current_app.logger.error(f"AI assistant error: {e}")
        return jsonify({'success': False, 'message': 'Assistant is temporarily unavailable. Please try again.'})


def get_fallback_response(message: str, context: dict) -> str:
    """Intelligent rule-based fallback when Watsonx is not configured."""
    msg = message.lower()
    diet = context.get('diet_preference', 'veg')

    # Recipe requests
    if any(kw in msg for kw in ['recipe', 'ingredient', 'make', 'cook', 'prepare']):
        if 'dal makhani' in msg:
            return ("🍛 **Dal Makhani Shopping List:**\n\n"
                    "1. Whole black urad dal (500g)\n"
                    "2. Rajma / kidney beans (100g)\n"
                    "3. Butter (100g)\n"
                    "4. Fresh cream (100ml)\n"
                    "5. Tomatoes (3 medium)\n"
                    "6. Onions (2 medium)\n"
                    "7. Ginger-garlic paste\n"
                    "8. Red chilli powder\n"
                    "9. Kashmiri red chilli\n"
                    "10. Garam masala\n"
                    "11. Kasuri methi\n\n"
                    "💡 Tip: Soak dal overnight for best results!")
        if 'biryani' in msg:
            return ("🍚 **Chicken/Veg Biryani Shopping List:**\n\n"
                    "1. Basmati rice (500g)\n"
                    "2. Onions (4 large)\n"
                    "3. Tomatoes (2)\n"
                    "4. Whole spices (bay leaf, cardamom, cloves, cinnamon)\n"
                    "5. Biryani masala\n"
                    "6. Saffron / food color\n"
                    "7. Mint leaves\n"
                    "8. Curd (200g)\n"
                    "9. Ghee (50g)\n"
                    "10. Fried onions\n\n"
                    "🛒 All available on FreshMart!")
        if 'gujarati' in msg or 'thali' in msg:
            return ("🥗 **Gujarati Thali Shopping List:**\n\n"
                    "1. Toor dal\n2. Bajra flour\n3. Methi (fenugreek leaves)\n"
                    "4. Undhiyu masala\n5. Jaggery\n6. Groundnut oil\n"
                    "7. Kokum\n8. Mustard seeds\n9. Curry leaves\n"
                    "10. Green chilies\n11. Sesame seeds\n12. Hing (asafoetida)\n\n"
                    "✨ Perfect for a traditional Gujarati meal!")
        return ("👨‍🍳 I'd love to help with your recipe! Here are some popular choices:\n\n"
                "• Dal Makhani 🍛\n• Chicken Biryani 🍚\n• Gujarati Thali 🥗\n• Chole Bhature 🫕\n\n"
                "Just ask: *'Ingredients for [dish name]'*")

    # Diwali / festival specials
    if any(kw in msg for kw in ['diwali', 'festival', 'festival shopping']):
        return ("🎉 **Diwali Special Shopping List:**\n\n"
                "🍬 Sweets: Mawa, Besan, Sugar, Khoya\n"
                "🥜 Dry Fruits: Cashews, Almonds, Raisins, Pistachios\n"
                "🫙 Extras: Ghee, Food colors, Silver warq\n"
                "🪔 Pooja: Camphor, Diyas, Incense sticks\n\n"
                "🛒 Shop our Diwali Specials for exclusive combos and discounts!")

    # Health / diet requests
    if any(kw in msg for kw in ['healthy', 'diet', 'weight loss', 'low calorie', 'keto', 'diabetic']):
        return ("🥦 **Healthy Grocery Suggestions:**\n\n"
                "🥬 Vegetables: Spinach, Broccoli, Capsicum, Beans\n"
                "🌾 Grains: Brown rice, Quinoa, Oats, Millets\n"
                "🥛 Protein: Paneer, Tofu, Lentils, Greek yogurt\n"
                "🫒 Healthy Fats: Olive oil, Avocado, Nuts\n"
                "🍎 Fruits: Berries, Apple, Papaya, Pomegranate\n\n"
                f"💡 Based on your {diet} preference, I've kept the list suitable for you!")

    # Budget shopping
    if any(kw in msg for kw in ['budget', 'cheap', '200', '500', 'affordable', 'economy']):
        return ("💰 **Budget Grocery List (Under ₹500):**\n\n"
                "1. Rice 5kg — ₹180\n"
                "2. Toor dal 1kg — ₹120\n"
                "3. Mustard oil 1L — ₹90\n"
                "4. Onions 2kg — ₹40\n"
                "5. Tomatoes 1kg — ₹30\n"
                "6. Mixed spices pack — ₹35\n\n"
                "Total ≈ ₹495 | Saves up to 20% with FreshMart deals! 🎯")

    # Substitution requests
    if any(kw in msg for kw in ['substitute', 'replace', 'instead of', 'alternative', 'swap']):
        substitutes = AGENT_CONFIG['substitutions']['substitute_map']
        for original, subs in substitutes.items():
            if original in msg:
                return (f"🔄 **Substitute for {original.title()}:**\n\n"
                        f"Try: {', '.join(subs)}\n\n"
                        f"All available on FreshMart! 🛒")
        return ("🔄 **Common Substitutes:**\n\n"
                "• Butter → Ghee or Coconut oil\n"
                "• Sugar → Jaggery or Honey\n"
                "• Paneer → Tofu\n"
                "• Cream → Coconut cream or Thick curd\n"
                "• Refined oil → Cold-pressed groundnut oil\n\n"
                "Need a specific substitute? Just ask! 😊")

    # Jain filter
    if 'jain' in msg:
        return ("🙏 **Jain-Friendly Shopping List:**\n\n"
                "✅ Allowed: All dals & lentils, Grains, Dairy, Above-ground vegetables\n"
                "✅ Fruits: All fresh fruits\n"
                "✅ Dry fruits: Cashews, Almonds, Raisins\n\n"
                "❌ Avoid: Onion, Garlic, Potato, Carrot, Beet, Radish, Turmeric (root)\n\n"
                "🛒 Use the 'Jain' filter on FreshMart to see only Jain-compatible products!")

    # Order tracking
    if any(kw in msg for kw in ['track', 'order', 'delivery', 'where is my']):
        return ("📦 **Track Your Order:**\n\n"
                "1. Go to **My Orders** in your profile\n"
                "2. Click on any order to see live tracking\n"
                "3. Or use the order number directly: /orders/track/[ORDER_NUMBER]\n\n"
                "📱 You'll receive updates at each step: Placed → Packed → Out for Delivery → Delivered!")

    # Greeting
    if any(kw in msg for kw in ['hello', 'hi', 'hey', 'namaste', 'good morning', 'good evening']):
        name = 'there'
        return (f"🙏 Namaste {name}! I'm **Freshie**, your FreshMart AI Shopping Assistant!\n\n"
                "I can help you with:\n"
                "🛒 Finding products\n"
                "👨‍🍳 Recipe-based shopping lists\n"
                "🔄 Product substitutions\n"
                "💰 Budget grocery planning\n"
                "🥗 Diet-based recommendations\n\n"
                "What can I help you with today? 😊")

    # Default helpful response
    return ("🤖 I'm **Freshie**, your FreshMart AI Assistant! I can help with:\n\n"
            "• 🍛 Recipe shopping lists (try: *'ingredients for Dal Makhani'*)\n"
            "• 🔄 Product substitutions (*'replace for butter'*)\n"
            "• 💰 Budget shopping (*'groceries under ₹500'*)\n"
            "• 🥗 Healthy alternatives (*'low-oil cooking options'*)\n"
            "• 🎉 Festival specials (*'Diwali shopping list'*)\n\n"
            "How can I assist you today? 😊")


@ai_bp.route('/quick-replies', methods=['GET'])
def quick_replies():
    return jsonify({'replies': AGENT_CONFIG['quick_replies']})
