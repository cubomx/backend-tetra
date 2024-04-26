from django.urls import path

from . import views

urlpatterns = [
    path('addCompra', views.addCompra, name='addCompra'),
    #path('getAbono', views.getAbono, name='getAbono'),
    #path('delAbono', views.delAbono, name='delAbono')
]
