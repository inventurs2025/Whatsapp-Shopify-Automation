from django.db import models

# Create your models here.

class Product(models.Model):
    sender = models.CharField(max_length=255)
    description = models.TextField()
    images = models.JSONField(default=list)  # Store image filenames as JSON array
    timestamp = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Product from {self.sender} - {self.created_at}"
    
    class Meta:
        ordering = ['-created_at']
