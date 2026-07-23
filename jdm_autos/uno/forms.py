from django import forms # type: ignore
from django.contrib.auth.forms import UserCreationForm # type: ignore
from django.contrib.auth import get_user_model # type: ignore
from django.forms import inlineformset_factory # type: ignore

from .models import CarListing, Inquiry, Profile,CarListingImage

User = get_user_model()


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(required=False)
    location = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'phone', 'location')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            Profile.objects.get_or_create(
                user=user,
                defaults={
                    'role': 'buyer',
                    'status': 'pending',
                    'phone': self.cleaned_data['phone'],
                    'location': self.cleaned_data['location'],
                },
            )
        return user


class CarListingForm(forms.ModelForm):
    class Meta:
        model = CarListing
        fields = ['title', 'brand', 'model', 'year', 'mileage', 'price', 'description', 'location', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),}
CarListingImageFormSet = inlineformset_factory(
    CarListing,
    CarListingImage,
    fields=["image"],
    extra=3,          # show 3 empty slots by default
    can_delete=True
)    
        


class InquiryForm(forms.ModelForm):
    class Meta:
        model = Inquiry
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3}),
        }
