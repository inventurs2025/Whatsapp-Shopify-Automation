from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Product
from django.utils import timezone

# ✅ External dependencies
import cloudinary.uploader
import requests
import json
import base64
from io import BytesIO

# ✅ Load environment variables
import os
from dotenv import load_dotenv
load_dotenv()

# ✅ Google Gemini
import google.generativeai as genai
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# --- Upload base64 image to Cloudinary ---
def upload_to_cloudinary_base64(image_obj):
    decoded = base64.b64decode(image_obj['base64'])
    result = cloudinary.uploader.upload(
        BytesIO(decoded),
        public_id=image_obj['filename'].split('.')[0],
        resource_type='image'
    )
    return result["secure_url"]

# --- Use Gemini to extract product fields ---
def parse_with_gemini(description):
    prompt = f"""
You are a Shopify product parser. The input is a product description from a vendor sent on WhatsApp.

Extract and return:
- title: A clean short title like "Pure Gajji Silk Banarasi Saree"
- body_html: Use HTML formatting for fabric, blouse, and work
- price: ONLY extract from SP / Sp / Selling Price (ignore CP, Cost Price)
- size: Always return "Free Size"

If SP or Selling Price is missing, leave "price" as "0".

Clean the price by extracting only digits (e.g., "Sp - 12800/-" → "12800").

Input:
\"\"\"
{description}
\"\"\"

Only respond with valid JSON like:
{{
  "title": "...",
  "body_html": "...",
  "price": "...",
  "size": "Free Size"
}}
"""

    model = genai.GenerativeModel("models/gemini-1.5-flash")
    response = model.generate_content(prompt)

    import re
    try:
        json_text = re.search(r'{.*}', response.text, re.DOTALL).group()
        return json.loads(json_text)
    except Exception:
        raise Exception("Gemini response format invalid:\n" + response.text)


# --- Send to Shopify ---
def send_to_shopify(product_data, image_urls):
    shopify_store = os.getenv("SHOPIFY_STORE_DOMAIN")
    shopify_api_key = os.getenv("SHOPIFY_API_KEY")
    shopify_password = os.getenv("SHOPIFY_API_PASSWORD")

    shopify_url = f"https://{shopify_store}/admin/api/2024-01/products.json"

    shopify_payload = {
        "product": {
            "title": product_data["title"],
            "body_html": product_data["body_html"],
            "images": [{"src": url} for url in image_urls],
            "variants": [{
                "price": product_data.get("price", "0.00"),
                "option1": product_data.get("size", "Free Size")
            }]
        }
    }

    r = requests.post(
        shopify_url,
        auth=(shopify_api_key, shopify_password),
        headers={"Content-Type": "application/json"},
        data=json.dumps(shopify_payload)
    )
    
    return r.json()

# --- Main API endpoint ---
@api_view(['POST'])
def add_product(request):
    print("🚀 /api/add-product/ was HIT!")
    data = request.data

    images = data.get('images', [])
    description = data.get('description', '').strip()
    sender = data.get('sender', '')
    timestamp = data.get('timestamp', '')

    if not images or not description or not sender:
        return Response({
            "status": "error", 
            "message": "Missing required fields: images, description, or sender"
        }, status=400)

    try:
        # Save product to DB (history)
        product = Product.objects.create(
            sender=sender,
            description=description,
            images=[img['filename'] for img in images],
            timestamp=timezone.now()
        )

        # Step 1: Upload images to Cloudinary
        image_urls = [upload_to_cloudinary_base64(img) for img in images]

        # Step 2: Parse description using Gemini
        product_data = parse_with_gemini(description)

        # Step 3: Send to Shopify
        shopify_response = send_to_shopify(product_data, image_urls)

        return Response({
            "status": "success",
            "message": "Product saved and sent to Shopify",
            "product_id": product.id,
            "shopify_response": shopify_response
        })

    except Exception as e:
        print("❌ Error:", str(e))
        return Response({
            "status": "error",
            "message": str(e)
        }, status=500)

# --- GET all products ---
@api_view(['GET'])
def get_products(request):
    products = Product.objects.all()
    data = []
    for product in products:
        data.append({
            'id': product.id,
            'sender': product.sender,
            'description': product.description,
            'images': product.images,
            'timestamp': product.timestamp,
            'created_at': product.created_at
        })
    return Response({"status": "success", "products": data})
