from django.contrib.auth import get_user_model # type: ignore
from django.db import models # type: ignore
from django.db.models.signals import post_save # type: ignore
from django.dispatch import receiver # type: ignore

User = get_user_model()


class Profile(models.Model):
    ROLE_CHOICES = [
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='buyer')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='approved')  # ✅ default approved
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


# 🔹 Auto-create a buyer profile when a new user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'profile'):
        Profile.objects.create(user=instance, role='buyer', status='approved')


class CarListing(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    title = models.CharField(max_length=200)
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    mileage = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    location = models.CharField(max_length=100)
    image = models.ImageField(upload_to='cars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class CarListingImage(models.Model):
    listing = models.ForeignKey(CarListing, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='cars/gallery/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Image for {self.listing.title}"


class Inquiry(models.Model):
    listing = models.ForeignKey(CarListing, on_delete=models.CASCADE, related_name='inquiries')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inquiries')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_inquiries', null=True, blank=True)
    message = models.TextField()
    reply = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    replied_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Inquiry for {self.listing.title}"
