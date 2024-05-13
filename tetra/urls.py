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
    path('finanzas/', include('gastos.urls')),
    path('finanzas/', include('abonos.urls')),
    path('agenda/', include('agenda.urls')),
    path('login', views.login, name='token_create'),
    path('register', views.register, name='create_user'),
    path('users', views.users, name='get users' ),
    path('addTipoEvento', views.addEventType, name='add type of event'),
    path('getTiposEvento', views.getEventTypes, name='get types of events'),
    path('delTipoEvento', views.delEventType, name='del type of event'),
    path('addLugar', views.addLocation, name='add location of event'),
    path('getLugares', views.getLocations, name='get locations of events'),
    path('delLugar', views.delLocation, name='del location of event'),
    path('editarUsuario', views.changePass, name='edit user')
]
