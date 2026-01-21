from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from project import settings


urlpatterns = [
    path("api/", include("apps.users.urls")),
    path("api/", include("apps.system_setting.urls")),
    path("api/", include("apps.cms.urls")),
    path("api/", include("apps.review.urls")),
    path("api/", include("apps.notifications.urls")),
    path("api/", include("apps.helpandsupport.urls")),
    path("api/prelaunch/", include("apps.prelaunch.urls")),
    path("api/", include("apps.manageai.urls")),
    path("api/", include("apps.task.urls")),
    path("api/", include("apps.subscription.urls")),
    path("api/", include("apps.socialauth.urls")),
    path("api/", include("apps.dashboard.urls")),

]

# Serve media files in both development and production
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]


urlpatterns += [
    path("", admin.site.urls),
]
