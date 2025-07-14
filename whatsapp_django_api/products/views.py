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

def generate_unique_sku():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

def parse_with_gemini(description):
    prompt = f"""
You are a Shopify product parser. Extract these from the following text:

- title: Short clean title
- body_html: Proper HTML format
- price: Sale price (SP / SALE PRICE / Selling Price)
- category: choose from [Ethnic, Western, Casual, Formal, Accessories]
- tags: comma-separated keywords or materials
- collections: comma-separated collections (like new, trending, banarasi)
- size: Always 'Free Size'

Text:
{description}

Respond in JSON like:
{{
  "title": "...",
  "body_html": "...",
  "price": "...",
  "size": "Free Size",
  "tags": "...",
  "category": "...",
  "collections": "..."
}}
"""
    model = genai.GenerativeModel("models/gemini-1.5-flash")
    response = model.generate_content(prompt)

    try:
        json_text = re.search(r'{.*}', response.text, re.DOTALL).group()
        return json.loads(json_text)
    except:
        return {}

def add_to_custom_collections(product_id, collections):
    shopify_url = f"https://{os.getenv('SHOPIFY_STORE_DOMAIN')}/admin/api/2024-01"
    auth = (os.getenv("SHOPIFY_API_KEY"), os.getenv("SHOPIFY_API_PASSWORD"))

    for title in collections.split(","):
        title = title.strip()
        if not title:
            continue

        res = requests.get(f"{shopify_url}/custom_collections.json?title={title}", auth=auth)
        coll = res.json().get("custom_collections", [])

        if not coll:
            create_res = requests.post(
                f"{shopify_url}/custom_collections.json",
                auth=auth,
                headers={"Content-Type": "application/json"},
                data=json.dumps({"custom_collection": {"title": title}})
            )
            coll = [create_res.json().get("custom_collection")]

        collection_id = coll[0].get("id")
        if not collection_id:
            continue

        payload = {
            "collect": {
                "product_id": product_id,
                "collection_id": collection_id
            }
        }
        requests.post(f"{shopify_url}/collects.json", auth=auth, headers={"Content-Type": "application/json"}, data=json.dumps(payload))

def send_to_shopify(data, image_urls):
    shopify_url = f"https://{os.getenv('SHOPIFY_STORE_DOMAIN')}/admin/api/2024-01/products.json"
    auth = (os.getenv("SHOPIFY_API_KEY"), os.getenv("SHOPIFY_API_PASSWORD"))

    price = str(data.get("price", "0"))
    compare_price = str(int(price) + 2000) if price.isdigit() else price
    sku = generate_unique_sku()

    payload = {
        "product": {
            "title": data.get("title", "Untitled Product"),
            "body_html": data.get("body_html", ""),
            "vendor": data.get("vendor", "DEFAULT"),
            "product_type": data.get("category", "Uncategorized"),
            "tags": data.get("tags", "") + ", India",
            "published_scope": "global",
            "status": "active",
            "images": [{"src": url} for url in image_urls],
            "options": [{"name": "Size", "values": [data.get("size", "Free Size")]}],
            "variants": [{
                "price": price,
                "compare_at_price": compare_price,
                "sku": sku,
                "taxable": False,
                "inventory_quantity": 5,
                "option1": data.get("size", "Free Size"),
                "weight": 2.0,
                "weight_unit": "kg",
                "requires_shipping": True,
                "harmonized_system_code": "620419"
            }]
        }
    }

    print("📦 Shopify payload:", json.dumps(payload, indent=2))
    r = requests.post(shopify_url, auth=auth, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
    result = r.json()
    product_id = result.get("product", {}).get("id")

    if product_id:
        add_to_custom_collections(product_id, data.get("collections", ""))

    return result, data["title"], price, sku, compare_price

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
            timestamp=timezone.now(),
            vendor=vendor
        )

        image_urls = [upload_to_cloudinary_base64(img) for img in images]
        parsed_data = parse_with_gemini(description)

        parsed_data.setdefault("title", "Ethnic Saree")
        parsed_data.setdefault("body_html", description.replace("\n", "<br>"))
        parsed_data.setdefault("price", "0")
        parsed_data.setdefault("size", "Free Size")
        parsed_data.setdefault("tags", "banarasi")
        parsed_data.setdefault("category", "Ethnic")
        parsed_data.setdefault("collections", "banarasi, trending")
        parsed_data["vendor"] = vendor

        print("🔍 Final parsed data:", parsed_data)

        shopify_response, title, price, sku, compare_price = send_to_shopify(parsed_data, image_urls)

        return Response({
            "status": "success",
            "shopify_data": {
                "title": title,
                "category": parsed_data["category"],
                "collections": parsed_data["collections"],
                "price": price,
                "compare_at_price": compare_price,
                "size": parsed_data["size"],
                "tags": parsed_data["tags"],
                "sku": sku,
                "vendor": vendor
            },
            "product_id": product.id
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
