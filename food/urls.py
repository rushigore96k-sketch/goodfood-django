from django.urls import path
from . import views

app_name = 'food'
urlpatterns = [
    path('', views.home, name='home'), path('menu/', views.menu, name='menu'),
    path('food/<int:pk>/', views.food_detail, name='food_detail'),
    path('register/', views.register_view, name='register'), path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'), path('about/', views.about, name='about'), path('contact/', views.contact, name='contact'),
    path('dashboard/', views.dashboard, name='dashboard'), path('profile/', views.profile, name='profile'),
    path('cart/', views.cart_view, name='cart'), path('cart/add/<int:pk>/', views.cart_add, name='cart_add'),
    path('cart/update/<int:pk>/', views.cart_update, name='cart_update'), path('cart/remove/<int:pk>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'), path('orders/', views.my_orders, name='orders'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'), path('orders/<int:pk>/success/', views.order_success, name='order_success'),
]
