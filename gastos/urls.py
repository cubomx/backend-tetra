from django.urls import path

from . import views

urlpatterns = [
    path('addGasto', views.addGasto, name='addGasto'),
    path('getGasto', views.getGasto, name='getGasto'),
    path('modifyGasto', views.modifyGasto, name='modifyGasto'),
    path('guardarEstadosResultados', views.guardarEstadoResultados, name='guardarEstadoResultados'),
    path('revertirMargenResultados', views.revertirMargenResultados, name='revertirMargenResultados'),
    path('getMargenResultados', views.getMargenResultados, name='getMargenResultados'),
    path('getTotales', views.getTotales, name='getTotales'),
    path('getEventData', views.getEventData, name='getEventData')
]
