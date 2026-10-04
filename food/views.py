from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from .forms import CheckoutForm, LoginForm, RegistrationForm
from .models import FoodCategory, FoodItem, Order, OrderItem, SiteContent, UserProfile

def home(request):
    foods = FoodItem.objects.filter(is_available=True, category__is_active=True).filter(
        Q(is_featured=True) | Q(is_popular=True)
    ).select_related('category').order_by('-is_popular', '-is_featured', 'name')[:6]
    if not foods.exists():
        foods = FoodItem.objects.filter(is_available=True, category__is_active=True).select_related('category').order_by('-created_at')[:6]
    content = SiteContent.objects.filter(pk=1, is_active=True).first()
    return render(request, 'food/home.html', {
        'categories': FoodCategory.objects.filter(is_active=True)[:6],
        'foods': foods,
        'site_content': content,
    })

def menu(request):
    foods = FoodItem.objects.select_related('category').filter(is_available=True, category__is_active=True)
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    sort = request.GET.get('sort', '')
    if query: foods = foods.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category.isdigit(): foods = foods.filter(category_id=int(category))
    if sort in ('price', '-price'): foods = foods.order_by(sort)
    return render(request, 'food/menu.html', {'foods': foods, 'categories': FoodCategory.objects.filter(is_active=True), 'query': query, 'selected_category': category, 'sort': sort})

def food_detail(request, pk):
    item = get_object_or_404(FoodItem, pk=pk, category__is_active=True)
    return render(request, 'food/food_detail.html', {'item': item})

def register_view(request):
    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Your account is ready.')
        return redirect('food:dashboard')
    return render(request, 'food/form_page.html', {'form': form, 'title': 'Create your account'})

def login_view(request):
    form = LoginForm(request.POST or None, request=request)
    if request.method == 'POST' and form.is_valid():
        login(request, form.cleaned_data['user'])
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
        return redirect('food:dashboard')
    return render(request, 'food/form_page.html', {'form': form, 'title': 'Welcome back'})

@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('food:home')

@login_required
def dashboard(request):
    return render(request, 'food/dashboard.html', {'orders': request.user.orders.all()[:5]})

def _cart(request): return request.session.setdefault('cart', {})

@require_POST
def cart_add(request, pk):
    item = get_object_or_404(FoodItem, pk=pk, is_available=True, category__is_active=True)
    cart = _cart(request)
    key = str(item.pk)
    try:
        quantity = int(cart.get(key, 0)) + int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 0
    if not 1 <= quantity <= 99:
        messages.error(request, 'Quantity must be between 1 and 99.')
    else:
        cart[key] = quantity
        request.session.modified = True
        messages.success(request, f'{item.name} added to your cart.')
    return redirect(request.POST.get('next') or 'food:cart')

def _cart_lines(request):
    cart = request.session.get('cart', {})
    items = FoodItem.objects.filter(pk__in=cart.keys(), is_available=True, category__is_active=True).select_related('category')
    lines = [{'item': item, 'quantity': int(cart[str(item.pk)]), 'subtotal': item.price * int(cart[str(item.pk)])} for item in items]
    total = sum((line['subtotal'] for line in lines), Decimal('0.00'))
    return lines, total

def cart_view(request):
    lines, total = _cart_lines(request)
    return render(request, 'food/cart.html', {'lines': lines, 'total': total})

@require_POST
def cart_update(request, pk):
    cart = request.session.get('cart', {})
    key = str(pk)
    try: quantity = int(request.POST.get('quantity', 0))
    except ValueError: quantity = 0
    if quantity <= 0: cart.pop(key, None)
    elif quantity <= 99 and FoodItem.objects.filter(pk=pk, is_available=True, category__is_active=True).exists(): cart[key] = quantity
    else: messages.error(request, 'That quantity is not valid or the item is unavailable.')
    request.session['cart'] = cart
    return redirect('food:cart')

@require_POST
def cart_remove(request, pk):
    cart = request.session.get('cart', {})
    cart.pop(str(pk), None)
    request.session['cart'] = cart
    return redirect('food:cart')

@login_required
def checkout(request):
    lines, total = _cart_lines(request)
    if not lines:
        messages.warning(request, 'Your cart is empty or its items are no longer available.')
        request.session['cart'] = {}
        return redirect('food:menu')
    initial = {'full_name': request.user.get_full_name(), 'contact_number': getattr(getattr(request.user, 'profile', None), 'contact_number', '')}
    form = CheckoutForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            locked = list(FoodItem.objects.select_for_update().filter(pk__in=[line['item'].pk for line in lines], is_available=True, category__is_active=True))
            if len(locked) != len(lines):
                messages.error(request, 'Some items became unavailable. Please review your cart.')
                return redirect('food:cart')
            order = form.save(commit=False)
            order.user = request.user
            total = sum((food.price * int(request.session.get('cart', {}).get(str(food.pk), 0)) for food in locked), Decimal('0.00'))
            order.total_amount = total
            order.save()
            if form.cleaned_data['full_name'] != request.user.get_full_name():
                request.user.first_name = form.cleaned_data['full_name']
                request.user.save(update_fields=['first_name'])
            for current in locked:
                quantity = int(request.session.get('cart', {}).get(str(current.pk), 0))
                OrderItem.objects.create(order=order, food_item=current, quantity=quantity, price=current.price)
            request.session['cart'] = {}
        return redirect('food:order_success', pk=order.pk)
    return render(request, 'food/checkout.html', {'form': form, 'lines': lines, 'total': total})

@login_required
def order_success(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, 'food/order_success.html', {'order': order})

@login_required
def my_orders(request):
    return render(request, 'food/orders.html', {'orders': request.user.orders.all()})

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related('items__food_item'), pk=pk, user=request.user)
    return render(request, 'food/order_detail.html', {'order': order})

@login_required
def profile(request):
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()[:150]
        email = request.POST.get('email', '').strip().lower()
        if not full_name or not email or request.user.__class__.objects.filter(email__iexact=email).exclude(pk=request.user.pk).exists():
            messages.error(request, 'Enter a name and unique email address.')
            return redirect('food:profile')
        request.user.first_name = full_name
        request.user.email = email
        request.user.save(update_fields=['first_name', 'email'])
        profile_obj.contact_number = request.POST.get('contact_number', '').strip()[:20]
        profile_obj.save(update_fields=['contact_number'])
        messages.success(request, 'Profile updated.')
        return redirect('food:profile')
    return render(request, 'food/profile.html', {'profile': profile_obj})

def about(request): return render(request, 'food/info.html', {'title': 'About us', 'body': 'Fresh meals from local kitchens, delivered with care.'})
def contact(request): return render(request, 'food/info.html', {'title': 'Contact', 'body': 'Questions about an order? Sign in and use My Orders to view its latest status.'})
