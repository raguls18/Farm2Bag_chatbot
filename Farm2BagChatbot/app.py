# Enhanced Farm2Bag Chatbot with improved features
from flask import Flask, request, jsonify, render_template, session
import requests, os, csv, json, re
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_change_this'

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAwRv53sBqgQuzK8GSjvcZ6UYZT3EcJKfA")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

# Load products from CSV with enhanced error handling
products_data = []
try:
    with open("cleaned_products.csv", "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            products_data.append({
                "Product Name": row.get("Product Name", "").strip(),
                "Price": float(row.get("Price", "0").replace(',', '')),
                "Stock": int(row.get("Stock", "0")),
                "Link": row.get("Link", "#"),
                "Image Link": row.get("Image Link", "")
            })
    print(f"✅ Loaded {len(products_data)} products successfully!")
except FileNotFoundError:
    print("❌ CSV file 'cleaned_products.csv' not found!")
except Exception as e:
    print(f"❌ Error loading products: {e}")

# Enhanced product search with fuzzy matching
def get_product_info(product_name):
    product_name = product_name.lower().strip()
    
    # Direct match first
    for product in products_data:
        if product_name in product["Product Name"].lower():
            return format_product_response(product)
    
    # Fuzzy search for better matches
    best_matches = []
    for product in products_data:
        product_words = product["Product Name"].lower().split()
        search_words = product_name.split()
        
        match_score = 0
        for search_word in search_words:
            for product_word in product_words:
                if search_word in product_word or product_word in search_word:
                    match_score += 1
        
        if match_score > 0:
            best_matches.append((product, match_score))
    
    if best_matches:
        # Return the product with highest match score
        best_product = max(best_matches, key=lambda x: x[1])[0]
        return format_product_response(best_product)
    
    return None

def format_product_response(product):
    """Format product response with enhanced information"""
    return {
        "product": product["Product Name"],
        "price": f"{product['Price']:.2f}",
        "stock": f"{product['Stock']} available" if product['Stock'] > 0 else "Out of stock",
        "link": product["Link"],
        "image": product.get("Image Link", ""),
        "stock_status": "in_stock" if product['Stock'] > 0 else "out_of_stock"
    }

# Enhanced query classification
def classify_user_query(user_message):
    user_message = user_message.lower().strip()
    
    query_patterns = {
        'order_tracking': ['where is my order', 'track my order', 'order status', 'my order', 'delivery status'],
        'cart_view': ['view cart', 'show cart', 'my cart', 'cart items'],
        'cart_clear': ['clear cart', 'empty cart', 'remove all'],
        'buy_now': ['buy now', 'purchase', 'buy this'],
        'add_to_cart': ['add to cart', 'add item'],
        'place_order': ['place order', 'checkout', 'order now'],
        'price_inquiry': ['price of', 'how much', 'cost of'],
        'stock_inquiry': ['stock', 'available', 'in stock'],
        'product_search': ['show me', 'find', 'search for'],
        'greeting': ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening'],
        'help': ['help', 'what can you do', 'commands', 'options']
    }
    
    for query_type, patterns in query_patterns.items():
        if any(pattern in user_message for pattern in patterns):
            return query_type
    
    return 'general'

# Enhanced Gemini API response with agriculture context
def get_gemini_response(user_input, context="agriculture"):
    try:
        # Add context for better agricultural responses
        contextual_prompt = f"""
        You are Farm2Bag's helpful agricultural assistant. You help farmers and customers with:
        - Product information about fruits and vegetables
        - Agricultural advice and farming tips
        - Order and delivery support
        - General farming guidance
        
        User query: {user_input}
        
        Respond in a friendly, helpful manner. Keep responses concise and practical.
        """
        
        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": contextual_prompt}]}]}
        
        response = requests.post(GEMINI_API_URL, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        ai_response = result['candidates'][0]['content']['parts'][0]['text'].strip()
        return ai_response
        
    except requests.exceptions.Timeout:
        return "⏰ Response taking longer than expected. Please try again."
    except requests.exceptions.RequestException as e:
        print(f"Gemini API Error: {e}")
        return "🤖 I'm experiencing some technical difficulties. Please try again in a moment."
    except Exception as e:
        print(f"Unexpected error: {e}")
        return "❌ Something went wrong. Please rephrase your question."

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_product', methods=['GET'])
def get_product():
    user_message = request.args.get("product", "").strip()
    if not user_message:
        return jsonify({"error": "No message provided."})

    # Classify the user query
    query_type = classify_user_query(user_message)
    
    # Handle different types of queries
    if query_type == 'order_tracking':
        return handle_order_tracking(user_message)
    elif query_type == 'cart_view':
        return view_cart()
    elif query_type == 'cart_clear':
        return clear_cart()
    elif query_type == 'buy_now':
        return buy_now(user_message)
    elif query_type == 'add_to_cart':
        return add_to_cart(user_message)
    elif query_type == 'place_order':
        return place_order()
    elif query_type == 'greeting':
        return handle_greeting()
    elif query_type == 'help':
        return show_help()
    elif query_type in ['price_inquiry', 'stock_inquiry', 'product_search']:
        return handle_product_query(user_message)
    else:
        # Try product search first, then AI response
        product = get_product_info(user_message)
        if product:
            return jsonify(product)
        else:
            ai_reply = get_gemini_response(user_message)
            return jsonify({"message": ai_reply})

def handle_greeting():
    return jsonify({
        "message": "🌾 Hello! Welcome to Farm2Bag! I'm here to help you with fresh fruits and vegetables. You can:\n\n🔍 Search for products\n🛒 Add items to cart\n💳 Place orders\n📦 Track deliveries\n🌱 Get farming advice\n\nWhat would you like to do today?"
    })

def show_help():
    return jsonify({
        "message": """🌾 **Farm2Bag Commands:**

🔍 **Product Search:**
- "Show me apples"
- "Price of bananas"
- "Stock of mangoes"

🛒 **Cart Management:**
- "Add apple to cart"
- "View my cart"
- "Clear cart"

💳 **Orders:**
- "Buy now [product]"
- "Place order"
- "Track my order"

🌱 **General:**
- Ask about farming tips
- Product recommendations
- Agricultural advice

Just type naturally - I'll understand! 😊"""
    })

def handle_product_query(user_message):
    # Extract product name from queries like "price of apple" or "stock of banana"
    patterns = [
        r'(?:price of|cost of|how much)\s+(.+)',
        r'(?:stock|available)\s+(.+)',
        r'(?:show me|find|search for)\s+(.+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, user_message.lower())
        if match:
            product_name = match.group(1).strip()
            product = get_product_info(product_name)
            if product:
                return jsonify(product)
    
    return jsonify({"message": "🤔 I couldn't find that product. Try searching with different keywords or ask me for help!"})

def handle_order_tracking(user_message):
    """Enhanced order tracking with realistic responses"""
    tracking_responses = [
        "📦 Your order is being prepared at our farm. Expected delivery: 2-3 days.",
        "🚛 Your order is out for delivery! You should receive it today.",
        "✅ Your order was delivered successfully. Thank you for choosing Farm2Bag!",
        "📋 We're processing your order. You'll receive tracking details via SMS/WhatsApp soon."
    ]
    
    import random
    response = random.choice(tracking_responses)
    
    return jsonify({
        "message": f"{response}\n\n💬 For detailed tracking, contact us on WhatsApp: +91 7305157325"
    })

def buy_now(message):
    # Extract product name
    product_name = re.sub(r'\b(?:buy now|buy|purchase)\b', '', message, flags=re.IGNORECASE).strip()
    
    if not product_name:
        return jsonify({"message": "❌ Please specify which product you'd like to buy."})
    
    product = get_product_info(product_name)
    if not product:
        return jsonify({"message": f"❌ Product '{product_name}' not found. Try searching for it first!"})
    
    if product["stock_status"] == "out_of_stock":
        return jsonify({"message": f"😞 Sorry, {product['product']} is currently out of stock."})
    
    return jsonify({
        "message": f"🛍️ Ready to buy <strong>{product['product']}</strong> for ₹{product['price']}!<br><br>📱 Complete your purchase via WhatsApp: <a href='https://wa.me/7305157325?text=I want to buy {product['product']}' target='_blank'>Order Now on WhatsApp</a>",
        "product_info": product
    })

def add_to_cart(message):
    # Extract product name
    product_name = re.sub(r'\b(?:add to cart|add)\b', '', message, flags=re.IGNORECASE).strip()
    
    if not product_name:
        return jsonify({"message": "❌ Please specify which product to add to cart."})
    
    product = get_product_info(product_name)
    if not product:
        return jsonify({"message": f"❌ Product '{product_name}' not found."})
    
    if product["stock_status"] == "out_of_stock":
        return jsonify({"message": f"😞 Sorry, {product['product']} is out of stock and cannot be added to cart."})
    
    # Initialize cart if it doesn't exist
    if "cart" not in session:
        session["cart"] = []
    
    # Check if product already in cart
    cart = session["cart"]
    for item in cart:
        if item["product"] == product["product"]:
            return jsonify({"message": f"ℹ️ {product['product']} is already in your cart!"})
    
    # Add to cart
    cart.append(product)
    session["cart"] = cart
    
    return jsonify({
        "message": f"✅ {product['product']} added to your cart! (₹{product['price']})\n\n📱 You can view your cart or proceed to checkout."
    })

def view_cart():
    cart = session.get("cart", [])
    if not cart:
        return jsonify({"message": "🛒 Your cart is empty. Browse our fresh products and add some!"})
    
    cart_msg = "🛍️ **Your Cart:**\n\n"
    total = 0
    
    for i, item in enumerate(cart, 1):
        price = float(item['price'])
        cart_msg += f"{i}. {item['product']} - ₹{item['price']}\n"
        total += price
    
    cart_msg += f"\n💰 **Total: ₹{total:.2f}**\n\n"
    cart_msg += "📱 Ready to order? Contact us on WhatsApp to complete your purchase!"
    
    return jsonify({"message": cart_msg})

def clear_cart():
    session["cart"] = []
    return jsonify({"message": "🗑️ Your cart has been cleared!"})

def place_order():
    cart = session.get("cart", [])
    if not cart:
        return jsonify({"message": "🛒 Your cart is empty. Please add items before placing an order."})
    
    # Calculate total
    total = sum(float(item['price']) for item in cart)
    
    # Create WhatsApp message with cart items
    whatsapp_message = "Hello Farm2Bag! I want to place an order:\n\n"
    for i, item in enumerate(cart, 1):
        whatsapp_message += f"{i}. {item['product']} - ₹{item['price']}\n"
    whatsapp_message += f"\nTotal: ₹{total:.2f}\n\nPlease confirm my order!"
    
    whatsapp_url = f"https://wa.me/7305157325?text={requests.utils.quote(whatsapp_message)}"
    
    # Clear cart after order
    session["cart"] = []
    
    return jsonify({
        "message": f"🎉 Order prepared! Total: ₹{total:.2f}<br><br>📱 <a href='{whatsapp_url}' target='_blank'>Complete Order on WhatsApp</a><br><br>Your cart has been cleared. Thank you for choosing Farm2Bag!"
    })

# New route for product suggestions
@app.route('/get_suggestions', methods=['GET'])
def get_suggestions():
    """Get product suggestions based on partial input"""
    query = request.args.get("q", "").lower()
    if len(query) < 2:
        return jsonify([])
    
    suggestions = []
    for product in products_data[:10]:  # Limit to first 10 matches
        if query in product["Product Name"].lower():
            suggestions.append({
                "name": product["Product Name"],
                "price": f"₹{product['Price']:.2f}"
            })
    
    return jsonify(suggestions)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)