from django.urls import path

from . import views

urlpatterns = [
    path('',views.index,name='index'),
    path('verAgenda',views.agenda,name='verAgenda'),
    path('addEvento', views.addEvento, name='addEvento'),
    path('delEvento', views.delEvento, name='delEvento'),
    path('getEvento', views.getEvento, name='getEvento'),
    path('modifyEvento', views.modifyEvento, name='modifyEvento'),
    path('calcularPaginacion', views.calculatePagination, name='CalculatePagination')
]
