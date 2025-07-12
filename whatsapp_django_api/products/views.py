# FILE: whatsapp_django_api/products/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Product
from django.utils import timezone

import cloudinary.uploader
import requests
import json
import base64
from io import BytesIO
import os
import random
import string
import re

from dotenv import load_dotenv
load_dotenv()

import google.generativeai as genai
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def upload_to_cloudinary_base64(image_obj):
    decoded = base64.b64decode(image_obj['base64'])
    result = cloudinary.uploader.upload(
        BytesIO(decoded),
        public_id=image_obj['filename'].split('.')[0],
        resource_type='image'
    )
    return result["secure_url"]

def parse_with_gemini(description):
    prompt = f"""
You are a Shopify product parser. The input is a product description from a vendor sent on WhatsApp.

Extract and return:
- title: A clean short title
- body_html: Format in HTML
- price: From SP / Sp / Selling Price (ignore CP)
- size: Always return "Free Size"
- tags: comma-separated list of keywords or materials
- category: choose from ethnic, western, casual, formal, accessories
- collections: comma-separated list if found

Input:
""" + description + """

Respond in JSON like:
{
  "title": "...",
  "body_html": "...",
  "price": "...",
  "size": "Free Size",
  "tags": "cotton, kurti",
  "category": "ethnic",
  "collections": "new, trending"
}
"""

    model = genai.GenerativeModel("models/gemini-1.5-flash")
    response = model.generate_content(prompt)

    try:
        json_text = re.search(r'{.*}', response.text, re.DOTALL).group()
        return json.loads(json_text)
    except Exception:
        raise Exception("Gemini response format invalid:\n" + response.text)

def generate_unique_sku():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

def send_to_shopify(data, image_urls):
    shopify_url = f"https://{os.getenv('SHOPIFY_STORE_DOMAIN')}/admin/api/2024-01/products.json"
    auth = (os.getenv("SHOPIFY_API_KEY"), os.getenv("SHOPIFY_API_PASSWORD"))

    price = str(data.get("price", "0"))
    compare_price = str(int(price) + 2000) if price.isdigit() else price

    payload = {
        "product": {
            "title": data["title"],
            "body_html": data["body_html"],
            "vendor": data.get("vendor", "DEFAULT"),
            "product_type": data.get("category", "Uncategorized"),
            "tags": data.get("tags", ""),
            "published_scope": "global",
            "status": "active",
            "images": [{"src": url} for url in image_urls],
            "options": [{"name": "Size", "values": [data.get("size", "Free Size")]}],
            "variants": [{
                "price": price,
                "compare_at_price": compare_price,
                "sku": generate_unique_sku(),
                "taxable": False,
                "inventory_quantity": 5,
                "option1": data.get("size", "Free Size"),
                "weight": 2.0,
                "weight_unit": "kg",
                "requires_shipping": True
            }]
        }
    }

    r = requests.post(shopify_url, auth=auth, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
    return r.json()

@api_view(['POST'])
def add_product(request):
    data = request.data
    images = data.get('images', [])
    description = data.get('description', '').strip()
    sender = data.get('sender', '')
    vendor = data.get('vendor', 'DEFAULT')

    if not images or not description or not sender:
        return Response({"status": "error", "message": "Missing required fields"}, status=400)

    try:
        product = Product.objects.create(
            sender=sender,
            description=description,
            images=[img['filename'] for img in images],
            timestamp=timezone.now()
        )

        image_urls = [upload_to_cloudinary_base64(img) for img in images]
        parsed_data = parse_with_gemini(description)
        parsed_data["vendor"] = vendor

        shopify_response = send_to_shopify(parsed_data, image_urls)

        return Response({
            "status": "success",
            "message": "Product sent to Shopify",
            "product_id": product.id,
            "shopify_response": shopify_response
        })

    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=500)

@api_view(['GET'])
def get_products(request):
    products = Product.objects.all()
    return Response({
        "status": "success",
        "products": [{
            "id": p.id,
            "sender": p.sender,
            "description": p.description,
            "images": p.images,
            "timestamp": p.timestamp,
            "created_at": p.created_at
        } for p in products]
    })
