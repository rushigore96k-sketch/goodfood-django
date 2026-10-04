from io import BytesIO
import tempfile
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from django.urls import reverse
from .models import FoodCategory, FoodItem, Order, OrderItem, SiteContent

User = get_user_model()

class FoodDeliveryTests(TestCase):
    def setUp(self):
        self.category = FoodCategory.objects.create(name='Pizza')
        self.food = FoodItem.objects.create(name='Garden Pizza', description='Fresh vegetables', category=self.category, price='250.00')
        self.user = User.objects.create_user(username='sam', password='Strong-password-91', email='sam@example.com')

    def test_registration_and_login(self):
        response = self.client.post(reverse('food:register'), {'first_name':'New Person','username':'newperson','email':'new@example.com','contact_number':'9876543210','password1':'LongPassword-12345','password2':'LongPassword-12345'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newperson').exists())
        self.client.logout()
        response = self.client.post(reverse('food:login'), {'username':'sam','password':'Strong-password-91'})
        self.assertEqual(response.status_code, 302)

    def test_menu_search_and_detail(self):
        self.assertContains(self.client.get(reverse('food:menu') + '?q=Garden'), 'Garden Pizza')
        self.assertEqual(self.client.get(reverse('food:food_detail', args=[self.food.pk])).status_code, 200)

    def test_cart_add_update_remove(self):
        self.client.force_login(self.user)
        self.client.post(reverse('food:cart_add', args=[self.food.pk]), {'quantity':2})
        self.assertEqual(self.client.session['cart'][str(self.food.pk)], 2)
        self.client.post(reverse('food:cart_update', args=[self.food.pk]), {'quantity':3})
        self.assertEqual(self.client.session['cart'][str(self.food.pk)], 3)
        self.client.post(reverse('food:cart_remove', args=[self.food.pk]))
        self.assertNotIn(str(self.food.pk), self.client.session['cart'])

    def test_checkout_creates_order_and_uses_current_price(self):
        self.client.force_login(self.user)
        self.client.post(reverse('food:cart_add', args=[self.food.pk]), {'quantity':2})
        self.food.price = '275.00'
        self.food.save()
        response = self.client.post(reverse('food:checkout'), {'full_name':'Sam Customer','contact_number':'9876543210','delivery_address':'12 Main Road'})
        order = Order.objects.get(user=self.user)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(order.total_amount, 550)
        self.assertEqual(order.items.get().price, 275)
        self.assertFalse(self.client.session['cart'])

    def test_orders_are_private(self):
        order = Order.objects.create(user=self.user, total_amount='250.00', delivery_address='Home', contact_number='9876543210')
        OrderItem.objects.create(order=order, food_item=self.food, quantity=1, price='250.00')
        other = User.objects.create_user(username='other', password='Strong-password-91')
        self.client.force_login(other)
        self.assertEqual(self.client.get(reverse('food:order_detail', args=[order.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('food:orders')).status_code, 200)

    def test_checkout_requires_login(self):
        self.assertEqual(self.client.get(reverse('food:checkout')).status_code, 302)

class RestaurantDashboardTests(TestCase):
    def setUp(self):
        self.category = FoodCategory.objects.create(name='Kitchen favorites')
        self.food = FoodItem.objects.create(name='Roasted Bowl', description='A warm seasonal bowl', category=self.category, price='320.00')
        self.customer = User.objects.create_user(username='customer', password='A-strong-password-2026', email='guest@example.com')
        self.staff = User.objects.create_user(username='manager', password='A-strong-password-2026', is_staff=True)
        self.admin = User.objects.create_superuser(username='owner', password='A-strong-password-2026', email='owner@example.com')

    def test_staff_area_redirects_anonymous_and_denies_customers(self):
        response = self.client.get(reverse('staff:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('food:login'), response.url)
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(reverse('staff:dashboard')).status_code, 403)

    def test_staff_login_returns_to_dashboard_but_rejects_external_redirects(self):
        response = self.client.post(reverse('food:login') + '?next=/manage/', {
            'username': 'manager', 'password': 'A-strong-password-2026', 'next': '/manage/',
        })
        self.assertRedirects(response, reverse('staff:dashboard'))
        self.client.logout()
        response = self.client.post(reverse('food:login'), {
            'username': 'manager', 'password': 'A-strong-password-2026', 'next': 'https://example.org/',
        })
        self.assertRedirects(response, reverse('food:dashboard'))

    def test_staff_dashboard_uses_real_records_and_admin_page_loads(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('staff:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Total orders')
        self.assertEqual(self.client.get('/admin/').status_code, 200)

    def test_all_staff_sections_render(self):
        self.client.force_login(self.staff)
        urls = ('staff:orders', 'staff:foods', 'staff:categories', 'staff:users', 'staff:website', 'staff:reports')
        for route in urls:
            with self.subTest(route=route):
                self.assertEqual(self.client.get(reverse(route)).status_code, 200)

    def test_food_and_category_crud_use_existing_models(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse('staff:food_add'), {
            'name': 'Citrus Salad', 'description': 'Bright and fresh', 'category': self.category.pk,
            'price': '210.00', 'is_available': 'on', 'is_featured': 'on', 'is_popular': 'on',
        })
        self.assertRedirects(response, reverse('staff:foods'))
        salad = FoodItem.objects.get(name='Citrus Salad')
        self.assertTrue(salad.is_featured)
        self.assertTrue(salad.is_popular)
        self.client.post(reverse('staff:category_edit', args=[self.category.pk]), {
            'name': 'Seasonal plates', 'description': 'Updated collection', 'is_active': 'on',
        })
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, 'Seasonal plates')
        # An in-use category is never removed out from under its food items.
        response = self.client.post(reverse('staff:category_delete', args=[self.category.pk]))
        self.assertRedirects(response, reverse('staff:categories'))
        self.assertTrue(FoodCategory.objects.filter(pk=self.category.pk).exists())

    def test_food_image_upload_uses_media_storage(self):
        image_buffer = BytesIO()
        Image.new('RGB', (1, 1), 'white').save(image_buffer, format='PNG')
        one_pixel_png = image_buffer.getvalue()
        self.client.force_login(self.staff)
        with tempfile.TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
            response = self.client.post(reverse('staff:food_add'), {
                'name': 'Image test', 'description': 'Uploaded from the staff editor', 'category': self.category.pk,
                'price': '120.00', 'is_available': 'on', 'image': SimpleUploadedFile('test.png', one_pixel_png, content_type='image/png'),
            })
            self.assertRedirects(response, reverse('staff:foods'), msg_prefix=str(response.context['form'].errors if response.context else ''))
            self.assertTrue(FoodItem.objects.get(name='Image test').image.name.startswith('foods/'))

    def test_food_in_order_history_cannot_be_deleted(self):
        self.client.force_login(self.staff)
        order = Order.objects.create(user=self.customer, total_amount='320.00', delivery_address='Address', contact_number='9876543210')
        OrderItem.objects.create(order=order, food_item=self.food, quantity=1, price='320.00')
        response = self.client.post(reverse('staff:food_delete', args=[self.food.pk]))
        self.assertRedirects(response, reverse('staff:foods'))
        self.assertTrue(FoodItem.objects.filter(pk=self.food.pk).exists())

    def test_order_status_and_user_access_updates(self):
        order = Order.objects.create(user=self.customer, total_amount='320.00', delivery_address='Address', contact_number='9876543210')
        OrderItem.objects.create(order=order, food_item=self.food, quantity=1, price='320.00')
        self.client.force_login(self.staff)
        response = self.client.post(reverse('staff:order_status', args=[order.pk]), {'status': Order.Status.PREPARING})
        self.assertRedirects(response, reverse('staff:order_detail', args=[order.pk]))
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PREPARING)
        self.client.post(reverse('staff:user_detail', args=[self.customer.pk]), {
            'first_name': 'Guest', 'last_name': 'Customer', 'email': 'guest@example.com', 'is_active': '',
        })
        self.customer.refresh_from_db()
        self.assertFalse(self.customer.is_active)
        self.assertEqual(self.client.get(reverse('staff:user_detail', args=[self.customer.pk])).status_code, 200)

    def test_only_superuser_can_change_staff_dashboard_access(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse('staff:user_detail', args=[self.customer.pk]), {
            'first_name': '', 'last_name': '', 'email': '', 'is_active': 'on', 'is_staff': 'on',
        })
        self.assertEqual(response.status_code, 302, response.context['form'].errors if response.context else '')
        self.customer.refresh_from_db()
        self.assertFalse(self.customer.is_staff)
        self.client.force_login(self.admin)
        response = self.client.post(reverse('staff:user_detail', args=[self.customer.pk]), {
            'first_name': '', 'last_name': '', 'email': '', 'is_active': 'on', 'is_staff': 'on',
        })
        self.assertEqual(response.status_code, 302, response.context['form'].errors if response.context else '')
        self.customer.refresh_from_db()
        self.assertTrue(self.customer.is_staff)

    def test_website_controls_homepage_and_featured_content(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse('staff:website'), {
            'hero_heading': 'Dinner, made lovely', 'hero_subheading': 'Fresh plates for your table.',
            'cta_label': 'See the menu', 'is_active': 'on',
        })
        self.assertRedirects(response, reverse('staff:website'))
        self.food.is_popular = True
        self.food.save()
        response = self.client.get(reverse('food:home'))
        self.assertContains(response, 'Dinner, made lovely')
        self.assertContains(response, 'Roasted Bowl')
        self.assertTrue(SiteContent.objects.filter(pk=1).exists())
