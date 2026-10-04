from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from django.db.models import Q
from .models import FoodCategory, FoodItem, Order, SiteContent, UserProfile

User = get_user_model()
phone_validator = RegexValidator(r'^\+?[0-9 ()-]{7,20}$', 'Enter a valid phone number.')
indian_mobile_validator = RegexValidator(
    r'^[6-9][0-9]{9}$',
    'Enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9.',
)

class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, label='Full name')
    email = forms.EmailField()
    contact_number = forms.CharField(
        max_length=10,
        required=True,
        error_messages={'required': 'Enter your 10-digit Indian mobile number.'},
        validators=[indian_mobile_validator],
    )
    class Meta:
        model = User
        fields = ('first_name', 'username', 'email', 'contact_number', 'password1', 'password2')
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            'first_name': 'Your full name',
            'username': 'Choose a username',
            'email': 'you@example.com',
            'password1': 'Create a password',
            'password2': 'Enter your password again',
        }
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
            if name in placeholders:
                field.widget.attrs['placeholder'] = placeholders[name]
    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists(): raise forms.ValidationError('An account with this email already exists.')
        return email
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            UserProfile.objects.update_or_create(user=user, defaults={'contact_number': self.cleaned_data['contact_number']})
        return user

class LoginForm(forms.Form):
    username = forms.CharField(label='Username or email')
    password = forms.CharField(widget=forms.PasswordInput)
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
    def clean(self):
        data = super().clean()
        identity, password = data.get('username'), data.get('password')
        if identity and password:
            user = User.objects.filter(email__iexact=identity).first() if '@' in identity else None
            data['user'] = authenticate(self.request, username=user.get_username() if user else identity, password=password)
            if data['user'] is None: raise forms.ValidationError('Invalid username/email or password.')
        return data

class CheckoutForm(forms.ModelForm):
    full_name = forms.CharField(max_length=150)
    class Meta:
        model = Order
        fields = ('delivery_address', 'contact_number')
        widgets = {'delivery_address': forms.Textarea(attrs={'rows': 3})}
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contact_number'].validators.append(phone_validator)

class FoodCategoryForm(forms.ModelForm):
    class Meta:
        model = FoodCategory
        fields = ('name', 'description', 'image', 'is_active')
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}

class FoodItemForm(forms.ModelForm):
    class Meta:
        model = FoodItem
        fields = ('name', 'description', 'category', 'price', 'image', 'is_available', 'is_featured', 'is_popular')
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        categories = FoodCategory.objects.filter(is_active=True)
        if self.instance and self.instance.pk:
            categories = FoodCategory.objects.filter(Q(is_active=True) | Q(pk=self.instance.category_id))
        self.fields['category'].queryset = categories

class SiteContentForm(forms.ModelForm):
    class Meta:
        model = SiteContent
        fields = ('hero_heading', 'hero_subheading', 'hero_image', 'cta_label', 'is_active')
        widgets = {'hero_subheading': forms.Textarea(attrs={'rows': 3})}

class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('status',)

class StaffUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'is_active')
    def __init__(self, *args, allow_staff_change=False, **kwargs):
        super().__init__(*args, **kwargs)
        if allow_staff_change:
            self.fields['is_staff'] = forms.BooleanField(required=False, label='Staff dashboard access', initial=self.instance.is_staff)
    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if email and User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Another account already uses this email.')
        return email
    def save(self, commit=True):
        person = super().save(commit=False)
        if 'is_staff' in self.cleaned_data:
            person.is_staff = self.cleaned_data['is_staff']
        if commit: person.save()
        return person
