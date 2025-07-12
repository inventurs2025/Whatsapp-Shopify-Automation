from django.urls import path
from .views import add_product, get_products

urlpatterns = [
    path('add-product/', add_product),
    path('get-products/', get_products),
]