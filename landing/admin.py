from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Brand, Product, RentalCategory

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    list_filter = ('is_active',)

class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    list_filter = ('is_active',)

class FeaturedProductFilter(admin.SimpleListFilter):
    title = 'Featured Status'
    parameter_name = 'featured_status'
    
    def lookups(self, request, model_admin):
        return (
            ('featured', 'Featured Products'),
            ('not_featured', 'Not Featured Products'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'featured':
            return queryset.filter(is_featured=True)
        if self.value() == 'not_featured':
            return queryset.filter(is_featured=False)
        return queryset

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'brand', 'stock', 'featured_status', 'is_active')
    list_filter = (FeaturedProductFilter, 'is_active', 'category', 'brand')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active',)
    actions = ['make_featured', 'remove_featured']
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'image', 'image_url')
        }),
        ('Pricing', {
            'fields': ('price', 'sale_price')
        }),
        ('Organization', {
            'fields': ('category', 'brand', 'stock')
        }),
        ('Status', {
            'fields': ('is_featured', 'is_active')
        }),
    )
    
    def featured_status(self, obj):
        if obj.is_featured:
            return format_html('<span style="background-color:#28a745; color:white; padding:5px 10px; border-radius:5px;">Featured</span>')
        return format_html('<span style="background-color:#6c757d; color:white; padding:5px 10px; border-radius:5px;">Not Featured</span>')
    
    featured_status.short_description = 'Featured'
    
    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} products have been marked as featured.')
    make_featured.short_description = "Mark selected products as featured"
    
    def remove_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} products have been removed from featured.')
    remove_featured.short_description = "Remove selected products from featured"

class RentalCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'daily_rate', 'weekly_rate', 'monthly_rate', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
    list_filter = ('is_active',)
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'image')
        }),
        ('Pricing', {
            'fields': ('daily_rate', 'weekly_rate', 'monthly_rate')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

admin.site.register(Category, CategoryAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(RentalCategory, RentalCategoryAdmin)