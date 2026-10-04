from django.core.management.base import BaseCommand
from food.models import FoodCategory, FoodItem

class Command(BaseCommand):
    help = 'Create example categories and menu items (safe to run more than once).'
    def handle(self, *args, **options):
        data = {
            'Pizza': [('Margherita Pizza', 'Tomato, mozzarella and basil.', '299.00'), ('Farmhouse Pizza', 'Garden vegetables with melted cheese.', '399.00')],
            'Burger': [('Classic Veg Burger', 'Crispy patty, lettuce and house sauce.', '179.00'), ('Smoky Chicken Burger', 'Grilled chicken with smoky mayo.', '249.00')],
            'Chinese': [('Chilli Garlic Noodles', 'Wok-tossed noodles with garlic and vegetables.', '229.00')],
            'South Indian': [('Masala Dosa', 'Crisp dosa with potato masala and chutneys.', '159.00')],
            'Desserts': [('Chocolate Brownie', 'Warm chocolate brownie.', '129.00')],
            'Beverages': [('Mango Lassi', 'Chilled yogurt drink with mango.', '99.00')],
        }
        for category_name, items in data.items():
            category, _ = FoodCategory.objects.get_or_create(name=category_name)
            for name, description, price in items:
                FoodItem.objects.get_or_create(name=name, category=category, defaults={'description': description, 'price': price})
        self.stdout.write(self.style.SUCCESS('Sample categories and food items are ready.'))
