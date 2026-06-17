from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny, IsAdminUser

schema_permission_classes = [AllowAny] if settings.PUBLIC_API_DOCS else [IsAdminUser]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(permission_classes=schema_permission_classes), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url="../schema/?format=json", permission_classes=schema_permission_classes),
        name="swagger-ui",
    ),
    path("api/", include("api.urls")),
]
