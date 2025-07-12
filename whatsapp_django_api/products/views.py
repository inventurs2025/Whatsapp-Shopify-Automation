from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Product
from django.utils import timezone

@api_view(['POST'])
def add_product(request):   
    print("🚀 /api/add-product/ was HIT!")
    data = request.data

    images = data.get('images', [])
    description = data.get('description', '').strip()
    sender = data.get('sender', '')
    timestamp = data.get('timestamp', '')

    # Validate required fields
    if not images or not description or not sender:
        return Response({
            "status": "error", 
            "message": "Missing required fields: images, description, or sender"
        }, status=400)

    try:
        # Create and save the product
        product = Product.objects.create(
            sender=sender,
            description=description,
            images=images,
            timestamp=timezone.now()
        )
        
        print("\n✅ New Product Saved to Database:")
        print("ID:", product.id)
        print("Sender:", product.sender)
        print("Description:", product.description)
        print("Images:", product.images)
        print("Timestamp:", product.timestamp)

        return Response({
            "status": "success", 
            "message": "Product saved successfully",
            "product_id": product.id
        })
        
    except Exception as e:
        print(f"❌ Error saving product: {e}")
        return Response({
            "status": "error", 
            "message": f"Failed to save product: {str(e)}"
        }, status=500)

@api_view(['GET'])
def get_products(request):
    """Get all products"""
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
