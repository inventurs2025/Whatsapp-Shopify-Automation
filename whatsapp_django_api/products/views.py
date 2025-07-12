from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Product
from django.utils import timezone

# ✅ External dependencies
import openai
import cloudinary.uploader
import requests
import json
import base64
from io import BytesIO

# ✅ Load environment variables
import os
from dotenv import load_dotenv
load_dotenv()

# --- Upload base64 image to Cloudinary ---
def upload_to_cloudinary_base64(image_obj):
    """
    image_obj = {
        'filename': 'img_123.jpg',
        'base64': '...',       # base64 string
        'mimetype': 'image/jpeg'
    }
    """
    decoded = base64.b64decode(image_obj['base64'])
    result = cloudinary.uploader.upload(
        BytesIO(decoded),
        public_id=image_obj['filename'].split('.')[0],
        resource_type='image'
    )
    return result["secure_url"]

# --- Use OpenAI to extract product fields ---
from openai import OpenAI

def parse_with_openai(description):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    system_prompt = "You are a Shopify product parser. Return JSON with: title, body_html, price, and size."
    user_prompt = f"""
Description:
\"\"\" 
{description}
\"\"\"

Return JSON like:
{{
  "title": "...",
  "body_html": "...",
  "price": "...",
  "size": "..."
}}"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3
    )

    return json.loads(response.choices[0].message.content)
# def parse_with_openai(description):
#     # FAKE hardcoded response for now (while fixing quota)
#     return {
#         "title": "Premium Handloom Banarasi Saree",
#         "body_html": "<p>100% Pure Tissue Handloom Banarasi Silk Saree with Zardozi, Pearl, Sequins work.</p>",
#         "price": "9800",
#         "size": "Free Size"
#     }


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

        # Step 2: Parse description
        product_data = parse_with_openai(description)

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

