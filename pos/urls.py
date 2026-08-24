from django.urls import path
from . import views

urlpatterns = [
    path('', views.pos_home, name='pos_home'),
    path('checkout/', views.checkout, name='checkout'),
    path("sales/", views.sales, name="sales"),
    
]