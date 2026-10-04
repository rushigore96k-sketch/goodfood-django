from django.urls import path
from . import staff_views

app_name = 'staff'
urlpatterns = [
    path('', staff_views.dashboard, name='dashboard'),
    path('orders/', staff_views.order_list, name='orders'),
    path('orders/<int:pk>/', staff_views.order_detail, name='order_detail'),
    path('orders/<int:pk>/status/', staff_views.order_status, name='order_status'),
    path('foods/', staff_views.food_list, name='foods'),
    path('foods/add/', staff_views.food_edit, name='food_add'),
    path('foods/<int:pk>/edit/', staff_views.food_edit, name='food_edit'),
    path('foods/<int:pk>/delete/', staff_views.food_delete, name='food_delete'),
    path('categories/', staff_views.category_list, name='categories'),
    path('categories/add/', staff_views.category_edit, name='category_add'),
    path('categories/<int:pk>/edit/', staff_views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', staff_views.category_delete, name='category_delete'),
    path('users/', staff_views.user_list, name='users'),
    path('users/<int:pk>/', staff_views.user_detail, name='user_detail'),
    path('website/', staff_views.website_management, name='website'),
    path('reports/', staff_views.reports, name='reports'),
    path('logout/', staff_views.staff_logout, name='logout'),
]
