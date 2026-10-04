from django.contrib import admin
from .models import FoodCategory, FoodItem, Order, OrderItem, SiteContent

@admin.register(FoodCategory)
class FoodCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('name',)

@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available', 'is_featured', 'is_popular', 'updated_at')
    list_filter = ('category', 'is_available', 'is_featured', 'is_popular')
    search_fields = ('name', 'description')
    list_editable = ('price', 'is_available')
    ordering = ('name',)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('food_item', 'quantity', 'price')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'order_date', 'total_amount', 'status')
    list_filter = ('status', 'order_date')
    search_fields = ('id', 'user__username', 'user__email', 'delivery_address')
    readonly_fields = ('user', 'order_date', 'total_amount', 'delivery_address', 'contact_number')
    inlines = (OrderItemInline,)
    ordering = ('-order_date',)

@admin.register(SiteContent)
class SiteContentAdmin(admin.ModelAdmin):
    list_display = ('hero_heading', 'is_active', 'updated_at')
    readonly_fields = ('updated_at',)
