"""cn_app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
import escapad_formulaire
#from escapad import views



urlpatterns = [
    #url(r'', include('django.contrib.auth.urls')),
    url(r'^', include('escapad.urls')),
    url(r'^admin/', admin.site.urls, name="admin"),
    url(r'^', include('escapad_formulaire.urls')),




]

admin.site.site_header = 'Esc@pad Admin'
admin.site.site_title = 'Esc@pad Admin'
