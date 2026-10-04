from datetime import timedelta
from functools import wraps
from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import redirect_to_login
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST
from .forms import FoodCategoryForm, FoodItemForm, OrderStatusForm, SiteContentForm, StaffUserForm
from .models import FoodCategory, FoodItem, Order, OrderItem, SiteContent

User = get_user_model()

def staff_only(view):
    @wraps(view)
    def guarded(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), reverse('food:login'))
        if not request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return guarded

def _admin(request, template, context=None):
    return render(request, f'food/staff/{template}.html', context or {})

@staff_only
def dashboard(request):
    delivered = Order.objects.filter(status=Order.Status.DELIVERED)
    status_summary = list(Order.objects.values('status').annotate(count=Count('id')).order_by('status'))
    order_count = sum(row['count'] for row in status_summary) or 1
    for row in status_summary: row['percent'] = round(row['count'] * 100 / order_count)
    return _admin(request, 'dashboard', {
        'total_orders': Order.objects.count(),
        'pending_orders': Order.objects.filter(status=Order.Status.PENDING).count(),
        'completed_orders': delivered.count(),
        'total_users': User.objects.count(),
        'total_foods': FoodItem.objects.count(),
        'total_categories': FoodCategory.objects.count(),
        'total_revenue': delivered.aggregate(value=Sum('total_amount'))['value'] or 0,
        'recent_orders': Order.objects.select_related('user').order_by('-order_date')[:8],
        'recent_users': User.objects.order_by('-date_joined')[:6],
        'popular_foods': OrderItem.objects.values('food_item__name').annotate(units=Sum('quantity')).order_by('-units')[:5],
        'status_summary': status_summary,
    })

@staff_only
def order_list(request):
    orders = Order.objects.select_related('user')
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    start = request.GET.get('start', '')
    end = request.GET.get('end', '')
    if query:
        search = Q(user__username__icontains=query) | Q(user__email__icontains=query) | Q(delivery_address__icontains=query)
        if query.isdigit(): search |= Q(pk=int(query))
        orders = orders.filter(search)
    if status in Order.Status.values: orders = orders.filter(status=status)
    if parse_date(start): orders = orders.filter(order_date__date__gte=parse_date(start))
    if parse_date(end): orders = orders.filter(order_date__date__lte=parse_date(end))
    return _admin(request, 'orders', {'orders': orders, 'query': query, 'status': status, 'start': start, 'end': end, 'statuses': Order.Status.choices})

@staff_only
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.select_related('user').prefetch_related('items__food_item'), pk=pk)
    return _admin(request, 'order_detail', {'order': order, 'status_form': OrderStatusForm(instance=order)})

@staff_only
@require_POST
def order_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    form = OrderStatusForm(request.POST, instance=order)
    if form.is_valid():
        form.save()
        messages.success(request, f'Order #{order.pk} status updated.')
    else:
        messages.error(request, 'Choose a valid order status.')
    return redirect('staff:order_detail', pk=pk)

@staff_only
def food_list(request):
    foods = FoodItem.objects.select_related('category')
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    availability = request.GET.get('availability', '')
    if query: foods = foods.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category.isdigit(): foods = foods.filter(category_id=int(category))
    if availability in ('true', 'false'): foods = foods.filter(is_available=(availability == 'true'))
    return _admin(request, 'foods', {'foods': foods, 'categories': FoodCategory.objects.all(), 'query': query, 'category': category, 'availability': availability})

@staff_only
def food_edit(request, pk=None):
    instance = get_object_or_404(FoodItem, pk=pk) if pk else None
    form = FoodItemForm(request.POST or None, request.FILES or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        item = form.save()
        messages.success(request, f'{item.name} saved.')
        return redirect('staff:foods')
    return _admin(request, 'form', {'form': form, 'title': 'Edit food item' if instance else 'Add food item', 'cancel_url': 'staff:foods'})

@staff_only
def food_delete(request, pk):
    item = get_object_or_404(FoodItem, pk=pk)
    if request.method == 'POST':
        if item.order_items.exists():
            messages.error(request, 'This item is part of order history and cannot be deleted. Mark it unavailable instead.')
            return redirect('staff:foods')
        item.delete()
        messages.success(request, 'Food item deleted.')
        return redirect('staff:foods')
    return _admin(request, 'confirm_delete', {'object': item, 'title': 'Delete food item', 'cancel_url': 'staff:foods', 'protected': item.order_items.exists()})

@staff_only
def category_list(request):
    categories = FoodCategory.objects.annotate(food_count=Count('items'))
    query = request.GET.get('q', '').strip()
    active = request.GET.get('active', '')
    if query: categories = categories.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if active in ('true', 'false'): categories = categories.filter(is_active=(active == 'true'))
    return _admin(request, 'categories', {'categories': categories, 'query': query, 'active': active})

@staff_only
def category_edit(request, pk=None):
    instance = get_object_or_404(FoodCategory, pk=pk) if pk else None
    form = FoodCategoryForm(request.POST or None, request.FILES or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        category = form.save()
        messages.success(request, f'{category.name} saved.')
        return redirect('staff:categories')
    return _admin(request, 'form', {'form': form, 'title': 'Edit category' if instance else 'Add category', 'cancel_url': 'staff:categories'})

@staff_only
def category_delete(request, pk):
    category = get_object_or_404(FoodCategory, pk=pk)
    if request.method == 'POST':
        if category.items.exists():
            messages.error(request, 'This category still contains food items. Reassign or delete them first.')
            return redirect('staff:categories')
        category.delete()
        messages.success(request, 'Category deleted.')
        return redirect('staff:categories')
    return _admin(request, 'confirm_delete', {'object': category, 'title': 'Delete category', 'cancel_url': 'staff:categories'})

@staff_only
def user_list(request):
    users = User.objects.all()
    query = request.GET.get('q', '').strip()
    active = request.GET.get('active', '')
    if query: users = users.filter(Q(username__icontains=query) | Q(email__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query))
    if active in ('true', 'false'): users = users.filter(is_active=(active == 'true'))
    return _admin(request, 'users', {'users': users.order_by('-date_joined'), 'query': query, 'active': active})

@staff_only
def user_detail(request, pk):
    person = get_object_or_404(User, pk=pk)
    form = StaffUserForm(request.POST or None, instance=person, allow_staff_change=request.user.is_superuser)
    if request.method == 'POST' and form.is_valid():
        if person.is_superuser and not form.cleaned_data.get('is_active', person.is_active):
            form.add_error('is_active', 'A superuser cannot be deactivated here.')
        if form.is_valid():
            form.save()
            messages.success(request, 'User details saved.')
            return redirect('staff:user_detail', pk=person.pk)
    contact_number = getattr(getattr(person, 'profile', None), 'contact_number', '')
    return _admin(request, 'user_detail', {
        'person': person, 'form': form, 'orders': person.orders.all()[:10],
        'contact_number': contact_number,
    })

@staff_only
def website_management(request):
    content, _ = SiteContent.objects.get_or_create(pk=1)
    form = SiteContentForm(request.POST or None, request.FILES or None, instance=content)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Homepage content updated.')
        return redirect('staff:website')
    return _admin(request, 'website', {
        'form': form,
        'featured_count': FoodItem.objects.filter(is_featured=True).count(),
        'popular_count': FoodItem.objects.filter(is_popular=True).count(),
        'active_categories': FoodCategory.objects.filter(is_active=True).count(),
    })

@staff_only
def reports(request):
    days = []
    today = timezone.localdate()
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        qs = Order.objects.filter(order_date__date=day)
        days.append({'date': day, 'orders': qs.count(), 'revenue': qs.filter(status=Order.Status.DELIVERED).aggregate(value=Sum('total_amount'))['value'] or 0})
    return _admin(request, 'reports', {'status_summary': Order.objects.values('status').annotate(count=Count('id'), amount=Sum('total_amount')).order_by('status'), 'days': days, 'revenue': Order.objects.filter(status=Order.Status.DELIVERED).aggregate(value=Sum('total_amount'))['value'] or 0})

@staff_only
@require_POST
def staff_logout(request):
    logout(request)
    return redirect('food:login')
