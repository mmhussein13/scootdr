from django.db import models
from django.utils.text import slugify
from django.urls import reverse
import os

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    logo = models.CharField(max_length=255, blank=True, null=True)  # Changed from ImageField to CharField
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    image = models.CharField(max_length=255, blank=True, null=True)  # Changed from ImageField to CharField
    # You can have an image URL instead of uploading an image
    image_url = models.CharField(max_length=255, blank=True, null=True, 
                               help_text="URL for the product image (used if no image is uploaded)")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products')
    stock = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_added']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('landing:product_detail', args=[self.id])
    
    def is_on_sale(self):
        return self.sale_price is not None and self.sale_price < self.price
    
    def get_display_price(self):
        if self.is_on_sale():
            return self.sale_price
        return self.price
    
    def get_image_url(self):
        """Returns either the uploaded image URL or the provided image URL"""
        if self.image_url:
            return self.image_url
        elif self.image:
            # The image field might be storing a path rather than using ImageField
            if hasattr(self.image, 'url'):
                return self.image.url
            else:
                return self.image  # If it's storing a path directly
        else:
            # Default image if none provided
            return '/static/images/products/placeholder.jpg'
    
    def __str__(self):
        return self.name


class RentalCategory(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    image = models.CharField(max_length=255, blank=True, null=True)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2)
    weekly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    monthly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Rental Categories"
        ordering = ['daily_rate']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_image_url(self):
        """Returns the image URL or a placeholder"""
        if self.image:
            if hasattr(self.image, 'url'):
                return self.image.url
            else:
                return self.image
        else:
            return '/static/images/rental/placeholder.jpg'
    
    def __str__(self):
        return self.name