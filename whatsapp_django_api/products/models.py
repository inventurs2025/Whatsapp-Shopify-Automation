from django.db import models

# Create your models here.

class Product(models.Model):
    sender = models.CharField(max_length=255)
    vendor = models.CharField(max_length=100, default='DEFAULT')
    description = models.TextField()
    images = models.JSONField(default=list)  # Store image filenames as JSON array
    timestamp = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # New fields for Shopify requirements
    hs_code = models.CharField(max_length=20, blank=True, null=True)
    variant = models.CharField(max_length=100, blank=True, null=True)
    colour = models.CharField(max_length=50, blank=True, null=True)
    metafields = models.JSONField(default=dict, blank=True)  # Store metafields as JSON
    page_description = models.TextField(blank=True, null=True)
    url_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    weight = models.FloatField(default=2.0)
    country = models.CharField(max_length=50, default='India')
    
    def __str__(self):
        return f"Product from {self.sender} - {self.created_at}"
    
    class Meta:
        ordering = ['-created_at']
