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
    try:
        decoded = base64.b64decode(image_obj['base64'])
        result = cloudinary.uploader.upload(
            BytesIO(decoded),
            public_id=image_obj['filename'].split('.')[0],
            resource_type='image'
        )
        print(f"✅ Uploaded to Cloudinary: {result['secure_url']}")
        return result["secure_url"]
    except Exception as e:
        print(f"❌ Cloudinary upload failed: {e}")
        raise

# def parse_with_gemini(description):
#     prompt = f"""
# You are a Shopify product parser. The input is a product description from a vendor sent on WhatsApp.

# Extract and return:
# - title: A clean short title
# - body_html: Format in HTML
# - price: From SP / Sp / Selling Price (ignore CP)
# - size: Always return "Free Size"
# - tags: comma-separated list of keywords or materials
# - category: choose from ethnic, western, casual, formal, accessories
# - collections: comma-separated list if found

# Input:
# {description}

# Respond in JSON like:
# {{
#   "title": "...",
#   "body_html": "...",
#   "price": "...",
#   "size": "Free Size",
#   "tags": "cotton, kurti",
#   "category": "ethnic",
#   "collections": "new, trending"
# }}
# """
#     try:
#         # model = genai.GenerativeModel("models/gemini-1.5-flash")
#         model = genai.GenerativeModel("models/gemini-1.5-pro")
#         response = model.generate_content(prompt)
#         print("🔍 Gemini raw response:", response.text)

#         json_text = re.search(r'{.*}', response.text, re.DOTALL).group()
#         parsed = json.loads(json_text)
#         print("✅ Parsed Gemini data:", parsed)
#         return parsed
#     except Exception as e:
#         print("❌ Gemini parsing failed:", str(e))
#         raise Exception("Gemini response failed due to: " + str(e))
#     # except Exception as e:
#     #     print("❌ Gemini parsing failed:", str(e))
#     #     raise Exception("Gemini response format invalid:\n" + response.text)


import openai
from openai import OpenAI
import os
import re
import json

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

def parse_with_groq(description):
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
{description}

Respond in JSON like:
{{
  "title": "...",
  "body_html": "...",
  "price": "...",
  "size": "Free Size",
  "tags": "cotton, kurti",
  "category": "ethnic",
  "collections": "new, trending"
}}
"""

    try:
        response = client.chat.completions.create(
            # model="mixtral-8x7b-32768",
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        content = response.choices[0].message.content
        print("🔍 Groq raw response:", content)

        json_text = re.search(r'{.*}', content, re.DOTALL).group()
        parsed = json.loads(json_text)
        print("✅ Parsed Groq data:", parsed)
        return parsed

    except Exception as e:
        print("❌ Groq parsing failed:", str(e))
        raise Exception("Groq response format invalid or failed")







def generate_unique_sku():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

def send_to_shopify(data, image_urls):
    try:
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

        print("📦 Shopify Payload:\n", json.dumps(payload, indent=2))

        r = requests.post(shopify_url, auth=auth, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
        print("📡 Shopify Response:", r.status_code, r.text)

        r.raise_for_status()
        return r.json(), data["title"], price
    except Exception as e:
        print("❌ Shopify upload failed:", str(e))
        raise

@api_view(['POST'])
def add_product(request):
    
    data = request.data
    images = data.get('images', [])
    description = data.get('description', '').strip()
    sender = data.get('sender', '')
    vendor = data.get('vendor', 'DEFAULT')

    print("📥 Received product from:", sender)
    print("📝 Description:", description)
    print(f"🖼️ Total images: {len(images)}")

    if not images or not description or not sender:
        return Response({"status": "error", "message": "Missing required fields"}, status=400)

    try:
        product = Product.objects.create(
            sender=sender,
            description=description,
            images=[img['filename'] for img in images],
            timestamp=timezone.now()
        )

        print("⬆️ Uploading images to Cloudinary...")
        image_urls = [upload_to_cloudinary_base64(img) for img in images]

        print("🧠 Parsing description using Groq...")
        # parsed_data = parse_with_gemini(description)
        parsed_data = parse_with_groq(description)
        parsed_data["vendor"] = vendor

        print("🚀 Sending product to Shopify...")
        shopify_response, title, price = send_to_shopify(parsed_data, image_urls)

        return Response({
            "status": "success",
            "message": "Product sent to Shopify",
            "product_id": product.id,
            "title": title,
            "price": price,
            "shopify_response": shopify_response
        })

    except Exception as e:
        print("❌ Internal Server Error:", str(e))
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
