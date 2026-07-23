from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import CarListing, CarListingImage, Profile


class MarketplaceFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='seller',
            email='seller@example.com',
            password='password123',
        )
        self.profile = Profile.objects.create(
            user=self.user,
            role='seller',
            status='approved',
            phone='09171234567',
            location='Quezon City',
        )
        self.listing = CarListing.objects.create(
            seller=self.user,
            title='Nissan Skyline R34',
            brand='Nissan',
            model='Skyline',
            year=1999,
            mileage=180000,
            price=2500000,
            description='Great condition and very clean.',
            location='Quezon City',
        )

    def test_homepage_shows_latest_listings(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nissan Skyline R34')

    def test_homepage_brand_cards_link_to_filtered_listings(self):
        response = self.client.get(reverse('home'))
        self.assertContains(response, reverse('listing_list') + '?brand=Toyota')
        self.assertContains(response, reverse('listing_list') + '?brand=Honda')

    def test_homepage_displays_listing_image_and_dollar_price(self):
        image = SimpleUploadedFile('car.jpg', b'file-content', content_type='image/jpeg')
        CarListing.objects.create(
            seller=self.user,
            title='Toyota Corolla',
            brand='Toyota',
            model='Corolla',
            year=2020,
            mileage=20000,
            price=900000,
            description='Reliable daily driver.',
            location='Makati',
            image=image,
        )

        response = self.client.get(reverse('home'))

        self.assertContains(response, '/media/cars/')
        self.assertContains(response, '$900,000.00')

    def test_detail_page_shows_listing_gallery(self):
        listing = CarListing.objects.create(
            seller=self.user,
            title='Honda Civic',
            brand='Honda',
            model='Civic',
            year=2021,
            mileage=15000,
            price=1200000,
            description='Well maintained car.',
            location='Taguig',
            image=SimpleUploadedFile('primary.jpg', b'primary', content_type='image/jpeg'),
        )
        CarListingImage.objects.create(
            listing=listing,
            image=SimpleUploadedFile('extra.jpg', b'extra', content_type='image/jpeg'),
        )

        response = self.client.get(reverse('listing_detail', args=[listing.pk]))

        self.assertContains(response, 'Vehicle overview')
        self.assertContains(response, '/media/cars/')
        self.assertContains(response, 'Honda Civic')

    def test_inquiry_submission_shows_success_message(self):
        buyer = get_user_model().objects.create_user(
            username='buyer',
            email='buyer@example.com',
            password='password123',
        )
        self.client.login(username='buyer', password='password123')

        response = self.client.post(
            reverse('send_inquiry', args=[self.listing.pk]),
            {'message': 'I am interested in this vehicle.'},
            follow=True,
        )

        self.assertContains(response, 'Your message was sent successfully')

    def test_filter_and_search_return_matching_listings(self):
        response = self.client.get(
            reverse('listing_list'),
            {
                'q': 'skyline',
                'brand': 'Nissan',
                'min_price': '2000000',
                'max_price': '3000000',
                'location': 'Quezon City',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nissan Skyline R34')

    def test_signup_defaults_new_users_to_buyer_role(self):
        response = self.client.post(
            reverse('signup'),
            {
                'username': 'newbuyer',
                'email': 'newbuyer@example.com',
                'password1': 'StrongPass123',
                'password2': 'StrongPass123',
                'phone': '09181234567',
                'location': 'Mandaluyong',
            },
        )

        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(username='newbuyer')
        self.assertTrue(Profile.objects.filter(user=user, role='buyer').exists())

    def test_non_seller_cannot_access_listing_creation(self):
        buyer = get_user_model().objects.create_user(
            username='buyer',
            email='buyer@example.com',
            password='password123',
        )
        Profile.objects.create(user=buyer, role='buyer', location='Pasig')
        self.client.login(username='buyer', password='password123')

        response = self.client.get(reverse('listing_create'))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_seller_can_create_and_view_dashboard(self):
        self.client.login(username='seller', password='password123')
        response = self.client.get(reverse('seller_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')

        response = self.client.post(
            reverse('listing_create'),
            {
                'title': 'Toyota Corolla',
                'brand': 'Toyota',
                'model': 'Corolla',
                'year': '2020',
                'mileage': '20000',
                'price': '900000',
                'description': 'Reliable daily driver.',
                'location': 'Makati',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CarListing.objects.filter(title='Toyota Corolla').exists())
