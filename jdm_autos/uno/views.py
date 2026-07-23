from django.contrib import messages # type: ignore
from django.contrib.auth import login, logout # type: ignore
from django.contrib.auth.decorators import login_required # type: ignore
from django.contrib.auth.forms import AuthenticationForm # type: ignore
from django.contrib.auth.models import User # type: ignore
from django.core.mail import send_mail # type: ignore
from django.shortcuts import get_object_or_404, redirect, render # type: ignore
from django.db.models import Q # type: ignore
from django.utils import timezone # type: ignore

from .forms import CarListingForm, InquiryForm, SignUpForm, CarListingImageFormSet
from .models import CarListing, CarListingImage, Inquiry, Profile


def home(request):
    listings = CarListing.objects.select_related('seller').all()[:6]
    return render(request, 'uno/home.html', {'listings': listings})


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.get_or_create(user=user, role='buyer', status='approved')
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'uno/auth_form.html', {'form': form, 'mode': 'signup'})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'uno/auth_form.html', {'form': form, 'mode': 'login'})


def logout_view(request):
    logout(request)
    return redirect('home')


def listing_list(request):
    query = request.GET.get('q', '')
    brand = request.GET.get('brand', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    location = request.GET.get('location', '')

    listings = CarListing.objects.select_related('seller').all()
    if query:
        listings = listings.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(brand__icontains=query))
    if brand:
        listings = listings.filter(brand__icontains=brand)
    if min_price:
        listings = listings.filter(price__gte=min_price)
    if max_price:
        listings = listings.filter(price__lte=max_price)
    if location:
        listings = listings.filter(location__icontains=location)

    return render(request, 'uno/listing_list.html', {
        'listings': listings,
        'query': query,
        'brand': brand,
        'min_price': min_price,
        'max_price': max_price,
        'location': location,
    })


def listing_detail(request, pk):
    listing = get_object_or_404(CarListing, pk=pk)
    gallery_images = list(listing.gallery_images.all())
    if listing.image and not gallery_images:
        gallery_images = [None]
    inquiry_form = InquiryForm()
    return render(request, 'uno/listing_detail.html', {'listing': listing, 'gallery_images': gallery_images, 'inquiry_form': inquiry_form, 'message_sent': False})

@login_required
def listing_create(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'seller' or profile.status != 'approved':
        return redirect('home')

    if request.method == 'POST':
        form = CarListingForm(request.POST, request.FILES)
        formset = CarListingImageFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            listing = form.save(commit=False)
            listing.seller = request.user
            listing.save()
            formset.instance = listing
            formset.save()
            for obj in formset.deleted_objects:
                obj.delete()
            return redirect('seller_dashboard')
    else:
        form = CarListingForm()
        formset = CarListingImageFormSet()
    return render(request, 'uno/listing_form.html', {'form': form, 'mode': 'create',"formset": formset})

@login_required
def listing_edit(request, pk):
    listing = get_object_or_404(CarListing, pk=pk, seller=request.user)
    if request.method == 'POST':
        form = CarListingForm(request.POST, request.FILES, instance=listing)
        formset = CarListingImageFormSet(request.POST, request.FILES, instance=listing)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            for obj in formset.deleted_objects:
              if obj.pk:
                obj.delete()
            return redirect('seller_dashboard')

    else:
        form = CarListingForm(instance=listing)
        formset = CarListingImageFormSet(instance=listing)
    return render(request, 'uno/listing_form.html', {'form': form,'formset': formset, 'mode': 'edit'})

@login_required
def listing_delete(request, pk):
    listing = get_object_or_404(CarListing, pk=pk, seller=request.user)
    if request.method == 'POST':
        listing.delete()
        return redirect('seller_dashboard')
    return render(request, 'uno/listing_confirm_delete.html', {'listing': listing})

@login_required
def seller_dashboard(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'seller' or profile.status != 'approved':
        return redirect('home')

    listings = CarListing.objects.filter(seller=request.user)
    return render(request, 'uno/seller_dashboard.html', {'listings': listings})

@login_required
def send_inquiry(request, pk):
    listing = get_object_or_404(CarListing, pk=pk)
    if request.method == 'POST':
        form = InquiryForm(request.POST)
        if form.is_valid():
            inquiry = Inquiry.objects.create(
                buyer=request.user,
                seller=listing.seller,
                listing=listing,
                message=form.cleaned_data['message'],
            )
            recipient = listing.seller.email if listing.seller.email else None
            if recipient:
                try:
                    send_mail(
                        subject=f'New inquiry for {listing.title}',
                        message=(
                            f'Hello {listing.seller.username},\n\n'
                            f'{request.user.username} sent you a new message about your listing "{listing.title}".\n\n'
                            f'Listing: {listing.title}\n'
                            f'Price: ${listing.price:.2f}\n'
                            f'Location: {listing.location}\n\n'
                            f'Message:\n{inquiry.message}\n\n'
                            f'Please log in to your account to reply.'
                        ),
                        from_email='no-reply@example.com',
                        recipient_list=[recipient],
                        fail_silently=False,
                    )
                except Exception:
                    pass
            messages.success(request, 'Your message was sent successfully. The seller will be notified shortly.')
            return redirect('listing_detail', pk=listing.pk)
    return redirect('listing_detail', pk=listing.pk)


@login_required
def inbox(request):
    profile = getattr(request.user, 'profile', None)
    if not profile:
        return redirect('home')

    if profile.role == 'seller' and profile.status == 'approved':
        # Seller inbox: inquiries received
        inquiries = Inquiry.objects.filter(seller=request.user).select_related('listing', 'buyer')
        return render(request, 'uno/inbox.html', {'inquiries': inquiries, 'mode': 'seller'})

    elif profile.role == 'buyer':
        # Buyer inbox: inquiries sent
        inquiries = Inquiry.objects.filter(buyer=request.user).select_related('listing', 'seller')
        return render(request, 'uno/inbox.html', {'inquiries': inquiries, 'mode': 'buyer'})

    else:
        return redirect('home')

@login_required
def inbox_detail(request, pk):
    inquiry = get_object_or_404(Inquiry, pk=pk)

    profile = getattr(request.user, 'profile', None)
    if not profile:
        return redirect('home')

    if profile.role == 'seller' and inquiry.seller == request.user:
        inquiry.is_read = True
        inquiry.save(update_fields=['is_read'])
        return render(request, 'uno/inbox_detail.html', {'inquiry': inquiry, 'mode': 'seller'})

    elif profile.role == 'buyer' and inquiry.buyer == request.user:
        inquiry.is_read = True
        inquiry.save(update_fields=['is_read'])
        return render(request, 'uno/inbox_detail.html', {'inquiry': inquiry, 'mode': 'buyer'})

    return redirect('home')

@login_required
def reply_inquiry(request, pk):
    inquiry = get_object_or_404(Inquiry, pk=pk)

    profile = getattr(request.user, 'profile', None)
    if profile.role == 'seller' and inquiry.seller == request.user:
        # seller replying to buyer
        if request.method == 'POST':
            reply = request.POST.get('reply', '').strip()
            if reply:
                inquiry.reply = reply
                inquiry.replied_at = timezone.now()
                inquiry.save(update_fields=['reply', 'replied_at'])
                send_mail(
                    subject=f'Re: {inquiry.listing.title}',
                    message=f'Seller {request.user.username} replied:\n\n{reply}',
                    from_email='no-reply@example.com',
                    recipient_list=[inquiry.buyer.email] if inquiry.buyer.email else [],
                    fail_silently=True,
                )
    elif profile.role == 'buyer' and inquiry.buyer == request.user:
        # buyer replying to seller
        if request.method == 'POST':
            reply = request.POST.get('reply', '').strip()
            if reply:
                inquiry.reply = reply
                inquiry.replied_at = timezone.now()
                inquiry.save(update_fields=['reply', 'replied_at'])
                send_mail(
                    subject=f'Re: {inquiry.listing.title}',
                    message=f'Buyer {request.user.username} replied:\n\n{reply}',
                    from_email='no-reply@example.com',
                    recipient_list=[inquiry.seller.email] if inquiry.seller.email else [],
                    fail_silently=True,
                )

    return redirect('inbox_detail', pk=inquiry.pk)
