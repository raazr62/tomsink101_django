from django.contrib import admin
from django.urls import path , include, re_path
from django.conf.urls.static import static
from project import settings
from django.views.static import serve


urlpatterns = [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    path('api/', include('apps.users.urls')),
    path('api/', include('apps.system_setting.urls')),
    path('api/', include('apps.cms.urls')),
    path('api/', include('apps.review.urls')),
    path('api/', include('apps.notifications.urls')),
    path('api/', include('apps.helpandsupport.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]


urlpatterns += [
    path("", admin.site.urls),
]