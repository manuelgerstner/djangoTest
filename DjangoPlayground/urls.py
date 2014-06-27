from django.conf import settings
from django.conf.urls import patterns, include, url
from DjangoTest import views


# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^DjangoTest/', include('DjangoTest.urls')),
                       url(r'^admin/', include(admin.site.urls)),
    # Examples:
    # url(r'^$', 'DjangoPlayground.views.home', name='home'),
    # url(r'^DjangoPlayground/', include('DjangoPlayground.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns(
        'django.views.static',
        (r'media/(?P<path>.*)',
        'serve',
        {'document_root': settings.MEDIA_ROOT}), )
