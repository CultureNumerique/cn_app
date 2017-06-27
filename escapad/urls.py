from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^build/(?P<slug>[\w-]+)/$',
        views.BuildView.as_view(),
        name='build_repo'),
    url(r'^buildzip/(?P<slug>[\w-]+)/$',
        views.BuildZipView.as_view(),
        name='build_zip_repo'),
    url(r'^site/(?P<slug>[\w-]+)/$',
        views.visit_site,
        name='visit_site'),
]
