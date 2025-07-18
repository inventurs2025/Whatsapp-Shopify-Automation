from django.db import models

# Create your models here.

class Product(models.Model):
    sender = models.CharField(max_length=255)
    vendor = models.CharField(max_length=100, default='DEFAULT')
    description = models.TextField()
    images = models.JSONField(default=list)  # Store image filenames as JSON array
    videos = models.JSONField(default=list)  # Store video filenames as JSON array
    timestamp = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Product from {self.sender} - {self.created_at}"
    
    class Meta:
        ordering = ['-created_at']
