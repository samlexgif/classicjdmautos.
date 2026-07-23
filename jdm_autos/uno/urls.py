from django.urls import path # type: ignore

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('listings/', views.listing_list, name='listing_list'),
    path('listings/<int:pk>/', views.listing_detail, name='listing_detail'),
    path('listings/new/', views.listing_create, name='listing_create'),
    path('listings/<int:pk>/edit/', views.listing_edit, name='listing_edit'),
    path('listings/<int:pk>/delete/', views.listing_delete, name='listing_delete'),
    path('dashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('inbox/', views.inbox, name='inbox'),
    path('inbox/<int:pk>/', views.inbox_detail, name='inbox_detail'),
    path('inbox/<int:pk>/reply/', views.reply_inquiry, name='reply_inquiry'),
    path('listings/<int:pk>/inquire/', views.send_inquiry, name='send_inquiry'),
]
