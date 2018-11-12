from django.urls import path
from rgt import views

urlpatterns = [
    path('', views.index, name='index')
]
