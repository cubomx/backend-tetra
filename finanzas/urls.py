from django.urls import path

from . import views

urlpatterns = [
    path('addAbono', views.addAbono, name='addAbono')
]
