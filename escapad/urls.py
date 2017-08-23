from django.conf.urls import url

from . import views

import escapad
from django.contrib.auth import views as auth_views

urlpatterns = [

    url(r'^$',
        escapad.views.index,
        name='index'),
    url(r'^help/$',
        escapad.views.help,
        name='help'),

    # Form views
    url(r'^course_from_uploaded_files/$',
        escapad.views.course_from_uploaded_files,
        name='course_from_uploaded_files'),
    url(r'^course_from_uploaded_archive/$',
        escapad.views.course_from_uploaded_archive,
        name='course_from_uploaded_archive'),
    url(r'^reupload/$',
        escapad.views.form_reupload,
        name='form_reupload'),
    url(r'^apercu_module/(?P<id_export>[-a-zA-Z\d]+)/(?P<feedback>[0-9])$',
        escapad.views.apercu_module,
        name='apercu_module'),
    url(r'^apercu_home/(?P<id_export>[-a-zA-Z\d]+)$',
        escapad.views.apercu_home,
        name='apercu_home'),


    # Studio
    url(r'^studio/$', escapad.views.studio, name='studio'),
    url(r'^cours/(?P<id_cours>[-a-zA-Z\d]+)$',
        escapad.views.cours,
        name='cours'),
    url(r'^cours/(?P<id_cours>[-a-zA-Z\d]+)/delete$',
        escapad.views.delete_course,
        name='delete_course'),
    url(r'^module/(?P<id_cours>[-a-zA-Z\d]+)/(?P<url>[-a-zA-Z\d]+)$',
        escapad.views.module,
        name='module'),
    url(r'^cours/(?P<id_cours>[-a-zA-Z\d]+)/(?P<url>[-a-zA-Z\d]+)/delete$',
        escapad.views.delete_module,
        name='delete_module'),

    # Repository views
    url(r'^repo/$',
        escapad.views.my_repositories,
        name='my_repositories'),
    url(r'^repo/(?P<slug>[\w-]+)/$',
        escapad.views.repository,
        name='repository'),
    url(r'^repo/(?P<slug>[\w-]+)/delete$',
        escapad.views.delete_repository,
        name='delete_repository'),

    # User views
    url(r'^connexion/$',
        escapad.views.connexion,
        name='connexion'),
    url(r'^deconnexion/$',
        escapad.views.deconnexion,
        name='deconnexion'),
    url(r'^inscription/$',
        escapad.views.inscription,
        name='inscription'),

    # Passwords
    url(r'^change_password/$', auth_views.password_change,
        {'template_name': 'escapad/password/password_change_form.html',
         'post_change_redirect': '/password_changed/'},
        name='change_password'),
    url(r'^password_changed/$',
        auth_views.password_change_done,
        {'template_name': 'escapad/password/password_change_done.html'},
        name='password_changed'),
    url(r'^password_reset/$', auth_views.password_reset,
        {'template_name': 'escapad/password/password_reset_form.html',
         'post_reset_redirect': '/password_reset/done/',
         'email_template_name': 'escapad/password/password_reset_email.html'},
        name='password_reset'),
    url(r'^password_reset/done/$',
        auth_views.password_reset_done,
        {'template_name': 'escapad/password/password_reset_done.html'},
        name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.password_reset_confirm,
        {'template_name': 'escapad/password/password_reset_confirm.html'},
        name='password_reset_confirm'),
    url(r'^reset/done/$',
        auth_views.password_reset_complete,
        {'template_name': 'escapad/password/password_reset_complete.html'},
        name='password_reset_complete'),
    url(r'^build/(?P<slug>[\w-]+)/$',
        views.BuildView.as_view(),
        name='build_repo'),
    url(r'^buildzip/(?P<slug>[\w-]+)/$',
        views.BuildZipView.as_view(),
        name='build_zip_repo'),
    url(r'^site/(?P<slug>[\w-]+)/$',
        views.visit_site,
        name='visit_site')
]
