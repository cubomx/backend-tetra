from django.urls import path

from . import views

urlpatterns = [
    path('addAbono', views.addAbono, name='addAbono'),
    path('getAbono', views.getAbono, name='getAbono'),
    path('delAbono', views.delAbono, name='delAbono'),
    path('editAbono', views.editAbono, name='editAbono'),
]
