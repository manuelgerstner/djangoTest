from django.conf.urls import patterns, url
from DjangoTest import views

urlpatterns = patterns('',
        url(r'^$', views.index, name='index'),
        # About page
        url(r'^about/', views.about, name='about'),
        url(r'^category/(?P<category_name_url>\w+)/$', views.category, name='category'))