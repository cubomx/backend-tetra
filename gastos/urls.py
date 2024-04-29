from django.urls import path

from . import views

urlpatterns = [
    path('addGasto', views.addGasto, name='addGasto'),
    path('getGasto', views.getGasto, name='getGasto'),
    #path('delAbono', views.delAbono, name='delAbono')
]
