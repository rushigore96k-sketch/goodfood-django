from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    contact_number = models.CharField(max_length=20, blank=True)
    def __str__(self): return f'{self.user.username} profile'

class FoodCategory(models.Model):
    name = models.CharField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'food categories'
    def __str__(self): return self.name

class FoodItem(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField()
    category = models.ForeignKey(FoodCategory, on_delete=models.PROTECT, related_name='items')
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    image = models.ImageField(upload_to='foods/', blank=True)
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_popular = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['name']
        indexes = [models.Index(fields=['is_available', 'category'])]
    def __str__(self): return self.name

class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        CONFIRMED = 'Confirmed', 'Confirmed'
        PREPARING = 'Preparing', 'Preparing'
        OUT_FOR_DELIVERY = 'Out for Delivery', 'Out for Delivery'
        DELIVERED = 'Delivered', 'Delivered'
        CANCELLED = 'Cancelled', 'Cancelled'
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='orders')
    order_date = models.DateTimeField(auto_now_add=True, db_index=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_address = models.TextField()
    contact_number = models.CharField(max_length=20)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.PENDING, db_index=True)
    class Meta: ordering = ['-order_date']
    def __str__(self): return f'Order #{self.pk}'

class SiteContent(models.Model):
    """Editable homepage copy and optional hero image; one row is used."""
    hero_heading = models.CharField(max_length=160, blank=True)
    hero_subheading = models.CharField(max_length=240, blank=True)
    hero_image = models.ImageField(upload_to='site/', blank=True)
    cta_label = models.CharField(max_length=40, blank=True, default='Explore the menu')
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return 'Homepage content'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    food_item = models.ForeignKey(FoodItem, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    @property
    def subtotal(self): return self.price * self.quantity
    def __str__(self): return f'{self.quantity} × {self.food_item.name}'
