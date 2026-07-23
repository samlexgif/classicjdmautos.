from django.contrib import admin # type: ignore

from .models import CarListing, Inquiry, Profile,CarListingImage


class CarListingImageInline(admin.TabularInline):  # or StackedInline
    model = CarListingImage
    extra = 3  # show 3 empty slots by default
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'status', 'location', 'phone')
    list_filter = ('role', 'status')
    search_fields = ('user__username', 'location')
    actions = ['approve_seller']

    def approve_seller(self, request, queryset):
        updated = queryset.update(role='seller', status='approved')
        self.message_user(request, f'{updated} profile(s) approved as seller.')

    approve_seller.short_description = 'Approve selected users as sellers'


@admin.register(CarListing)
class CarListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'brand', 'price', 'location', 'seller')
    search_fields = ('title', 'brand', 'seller__username')
    inlines = [CarListingImageInline]


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('listing', 'buyer', 'created_at')
    search_fields = ('message', 'buyer__username')
