from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Category, Brand, Product

# The following sample data functions will eventually be removed once we have real data in database
# Kept here temporarily for backwards compatibility
def get_sample_products():
    products = [
        {
            'id': 1,
            'name': 'Vespa Primavera 150',
            'description': 'The classic Italian scooter with modern features. Elegant, stylish, and perfect for city commuting.',
            'price': 4999.99,
            'image': '/static/images/products/vespa-primavera.jpg',
            'category': 'Commuter',
            'brand': 'Vespa',
            'in_stock': True
        },
        {
            'id': 2,
            'name': 'Honda PCX 125',
            'description': 'Economical and reliable city scooter with excellent fuel efficiency and storage space.',
            'price': 3499.99,
            'image': '/static/images/products/honda-pcx.jpg',
            'category': 'Commuter',
            'brand': 'Honda',
            'in_stock': True
        },
        {
            'id': 3,
            'name': 'Yamaha XMAX 300',
            'description': 'A sporty, high-performance scooter with advanced features and excellent stability.',
            'price': 5999.99,
            'image': '/static/images/products/yamaha-xmax.jpg',
            'category': 'Sport',
            'brand': 'Yamaha',
            'in_stock': True
        },
        {
            'id': 4,
            'name': 'BMW C 400 GT',
            'description': 'Premium mid-size touring scooter with exceptional comfort and advanced technology.',
            'price': 8999.99,
            'image': '/static/images/products/bmw-c400.jpg',
            'category': 'Touring',
            'brand': 'BMW',
            'in_stock': False
        }
    ]
    return products

def get_sample_rental_categories():
    categories = [
        {
            'id': 1,
            'name': 'Category A - Sym Orbit 125cc',
            'description': 'Economical 125cc scooters perfect for city trips and commuting. Easy to handle.',
            'image': '/static/images/rental/economy.jpg',
            'daily_rate': 400,
            'weekly_rate': 300 * 7,  # 300 per day for 2-10 days
            'monthly_rate': 120 * 30  # 120 per day for 30+ days
        },
        {
            'id': 2,
            'name': 'Category B - Jet 14 200cc',
            'description': 'Mid-size 200cc scooters with more power and comfort for longer journeys.',
            'image': '/static/images/rental/midsize.jpg',
            'daily_rate': 450,
            'weekly_rate': 350 * 7,  # 350 per day for 2-10 days
            'monthly_rate': 150 * 30  # 150 per day for 30+ days
        },
        {
            'id': 3,
            'name': 'Category C - Citycom 300cc',
            'description': 'Powerful 300cc scooters with enhanced comfort for city and highway riding.',
            'image': '/static/images/rental/premium.jpg',
            'daily_rate': 550,
            'weekly_rate': 500 * 7,  # 500 per day for 2-10 days
            'monthly_rate': 250 * 30  # 250 per day for 30+ days
        },
        {
            'id': 4,
            'name': 'Category D - Vespa 150/300cc',
            'description': 'Premium Vespa scooters with stylish Italian design and excellent performance.',
            'image': '/static/images/rental/vespa.jpg',
            'daily_rate': 850,
            'weekly_rate': 600 * 7,  # 600 per day for 2-10 days
            'monthly_rate': 250 * 30  # 250 per day for 30+ days
        }
    ]
    return categories

# Landing page views
def home(request):
    """Home page view displaying featured products and services"""
    # Check if there are any featured products in the database
    db_products_exist = Product.objects.filter(is_active=True, is_featured=True).exists()
    
    if db_products_exist:
        # Use featured products from the database
        featured_products = Product.objects.filter(is_active=True, is_featured=True)[:3]
    else:
        # Fallback to sample products if no featured products in database
        featured_products = get_sample_products()[:3]
    
    return render(request, 'landing/home.html', {
        'featured_products': featured_products
    })

def products(request):
    """Products listing page with filters"""
    # Check if there are any products in the database
    db_products_exist = Product.objects.filter(is_active=True).exists()
    
    if db_products_exist:
        # Use database products if they exist
        products = Product.objects.filter(is_active=True)
        
        # Handle filtering using database queries
        category_id = request.GET.get('category')
        brand_id = request.GET.get('brand')
        price_min = request.GET.get('price_min')
        price_max = request.GET.get('price_max')
        sort = request.GET.get('sort', 'popularity')
        
        # Apply filters
        if category_id:
            products = products.filter(category_id=category_id)
        if brand_id:
            products = products.filter(brand_id=brand_id)
        if price_min:
            products = products.filter(price__gte=float(price_min))
        if price_max:
            products = products.filter(price__lte=float(price_max))
        
        # Apply sorting
        if sort == 'price_low':
            products = products.order_by('price')
        elif sort == 'price_high':
            products = products.order_by('-price')
        elif sort == 'newest':
            products = products.order_by('-date_added')
        elif sort == 'popularity':
            # For now just sort by featured, later could be based on views or sales
            products = products.order_by('-is_featured', '-date_added')
        
        # Get all categories and brands for the filter dropdowns
        categories = Category.objects.filter(is_active=True)
        brands = Brand.objects.filter(is_active=True)
        
        # Popular products for sidebar (featured products)
        popular_products = Product.objects.filter(is_active=True, is_featured=True)[:3]
        
        # Pagination
        paginator = Paginator(products, 6)  # 6 products per page
        page_number = request.GET.get('page', 1)
        products_page = paginator.get_page(page_number)
        
        context = {
            'products': products_page,
            'categories': categories,
            'brands': brands,
            'popular_products': popular_products,
            'selected_category': category_id,
            'selected_brand': brand_id,
            'price_min': price_min,
            'price_max': price_max
        }
    else:
        # If no database products exist, use sample data
        sample_products = get_sample_products()
        paginator = Paginator(sample_products, 6)  # 6 products per page
        page_number = request.GET.get('page', 1)
        products_page = paginator.get_page(page_number)
        
        # Create sample categories and brands from sample products
        sample_categories = list(set(p['category'] for p in sample_products))
        sample_brands = list(set(p['brand'] for p in sample_products))
        
        context = {
            'products': products_page,
            'categories': sample_categories,
            'brands': sample_brands,
            'popular_products': sample_products[:3],
            'selected_category': request.GET.get('category'),
            'selected_brand': request.GET.get('brand'),
            'price_min': request.GET.get('price_min'),
            'price_max': request.GET.get('price_max'),
            'using_sample_data': True  # Flag to indicate we're using sample data
        }
    
    return render(request, 'landing/products.html', context)

def product_detail(request, product_id):
    """Individual product detail page"""
    try:
        # Get product from database - pass model object directly to template
        product = Product.objects.get(id=product_id)
        
        # Add additional template-needed fields 
        product.in_stock = product.stock > 0
        
        # Get related products from the same category
        related_products = Product.objects.filter(
            category=product.category
        ).exclude(id=product.id)[:3]
        
        # Add in_stock property to related products
        for prod in related_products:
            prod.in_stock = prod.stock > 0
            
    except Product.DoesNotExist:
        # If product not found, redirect to products page with error
        messages.error(request, "Product not found")
        return redirect('landing:products')
    
    context = {
        'product': product,
        'related_products': related_products
    }
    
    return render(request, 'landing/product_detail.html', context)

def buy(request):
    """Buy page with latest products and categories"""
    # Check if there are any products in the database
    db_products_exist = Product.objects.filter(is_active=True).exists()
    
    if db_products_exist:
        # Use database products if they exist, ordered by date added (newest first)
        latest_products = Product.objects.filter(is_active=True).order_by('-date_added')
    else:
        # Fallback to sample products if no database products exist
        latest_products = get_sample_products()
    
    context = {
        'latest_products': latest_products
    }
    
    return render(request, 'landing/buy.html', context)

def rent(request):
    """Rent page with rental options"""
    # Import here to avoid circular import
    from .models import RentalCategory
    
    # Check if there are any rental categories in the database
    db_rental_categories_exist = RentalCategory.objects.filter(is_active=True).exists()
    
    if db_rental_categories_exist:
        # Use database rental categories if they exist
        rental_categories = RentalCategory.objects.filter(is_active=True).order_by('daily_rate')
    else:
        # Fallback to sample rental categories if none exist in database
        rental_categories = get_sample_rental_categories()
    
    context = {
        'rental_categories': rental_categories
    }
    
    # Using the new rent page template with direct booking form
    return render(request, 'landing/rent_new.html', context)

def restore(request):
    """Restoration services page"""
    return render(request, 'landing/restore.html')

def service(request):
    """Service and maintenance page"""
    return render(request, 'landing/service_new.html')

def contact(request):
    """Contact us page"""
    # Handle form submission in a real app
    if request.method == 'POST':
        # Process contact form
        messages.success(request, "Your message has been sent. We'll be in touch soon!")
        return redirect('landing:contact')
    
    return render(request, 'landing/contact.html')

def account(request):
    """User account page - shows login form if not authenticated"""
    if not request.user.is_authenticated:
        return render(request, 'landing/login.html', {'next': request.path})
    
    # If user is authenticated, show their account
    # In a real app, this would fetch the user's orders, rentals, etc.
    context = {
        'user_scooters': [],  # User's registered scooters
        'orders': [],         # User's orders
        'rentals': [],        # User's rentals
        'services': [],       # User's service history
        'favorites': []       # User's favorite products
    }
    
    return render(request, 'landing/account.html', context)

def login_view(request):
    """Handle customer login"""
    if request.user.is_authenticated:
        return redirect('landing:account')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.POST.get('next', 'landing:account')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, 'landing/login.html', {'form_errors': True})
    
    # If not POST, show the login form
    return render(request, 'landing/login.html')

def register(request):
    """Handle user registration for customer accounts only"""
    if request.user.is_authenticated:
        return redirect('landing:account')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        terms_agreed = request.POST.get('terms')
        
        # Basic validation
        if not terms_agreed:
            messages.error(request, "You must agree to the terms and conditions.")
            return render(request, 'landing/login.html', {'register_error': "You must agree to the terms and conditions."})
        
        if password1 != password2:
            messages.error(request, "Passwords don't match.")
            return render(request, 'landing/login.html', {'register_error': "Passwords don't match."})
        
        # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, 'landing/login.html', {'register_error': "Username already taken."})
            
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, 'landing/login.html', {'register_error': "Email already registered."})
        
        # Create the user - this will be a regular user (customer), not staff
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
                is_staff=False  # Ensure this user is NOT staff
            )
            
            # Create customer profile if there's a customer model
            # This would be expanded in a real app
            
            # Log the user in after registration
            login(request, user)
            messages.success(request, f"Welcome to ScootDR, {user.first_name}! Your account has been created.")
            return redirect('landing:account')
            
        except Exception as e:
            messages.error(request, f"Error creating account: {str(e)}")
            return render(request, 'landing/login.html', {'register_error': f"Error creating account: {str(e)}"})
    
    # If not POST, redirect to login page with register tab active
    return redirect('landing:account')

def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('landing:home')

def terms(request):
    """Terms and conditions page"""
    return render(request, 'landing/terms.html')

def rental_terms(request):
    """Rental terms and conditions page"""
    return render(request, 'landing/rental_terms.html')

def financing(request):
    """Financing options page"""
    return render(request, 'landing/financing.html')

def maintenance_tips(request):
    """Maintenance tips page"""
    return render(request, 'landing/maintenance_tips.html')

def restoration_gallery(request):
    """Restoration gallery page"""
    return render(request, 'landing/restoration_gallery.html')

def password_reset(request):
    """Handle password reset requests"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            # In a real app, we would generate a token and send an email
            # For now, just show a success message
            messages.success(
                request,
                "If an account exists with this email, you will receive password reset instructions."
            )
            return redirect('landing:login')
        except User.DoesNotExist:
            # We don't want to reveal which emails are registered
            # So we show the same message even if the email doesn't exist
            messages.success(
                request,
                "If an account exists with this email, you will receive password reset instructions."
            )
            return redirect('landing:login')
    
    # If not POST, show the password reset form
    return render(request, 'landing/password_reset.html')