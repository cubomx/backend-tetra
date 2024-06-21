"""
URL configuration for tetra project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/finanzas/', include('gastos.urls')),
    path('api/finanzas/', include('abonos.urls')),
    path('api/agenda/', include('agenda.urls')),
    path('api/login', views.login, name='token_create'),
    path('api/register', views.register, name='create_user'),
    path('api/users', views.users, name='get users' ),
    path('api/addTipoEvento', views.addEventType, name='add type of event'),
    path('api/getTiposEvento', views.getEventTypes, name='get types of events'),
    path('api/delTipoEvento', views.delEventType, name='del type of event'),
    path('api/addLugar', views.addLocation, name='add location of event'),
    path('api/getLugares', views.getLocations, name='get locations of events'),
    path('api/delLugar', views.delLocation, name='del location of event'),
    path('api/editarUsuario', views.changePass, name='edit user'),
    path('api/delUsuario', views.delUsuario, name='del user'),
    path('api/addConcepto', views.addConcept, name='add concept of event'),
    path('api/getConceptos', views.getConcepts, name='get concepts of events'),
    path('api/delConcepto', views.delConcepts, name='del concept'),
    path('api/addProveedor', views.addProvider, name='add provider'),
    path('api/getProveedor', views.getProviders, name='get providers'),
    path('api/delProveedor', views.delProvider, name='del providers'),
]
