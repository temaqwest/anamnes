from django.urls import include, path
from django.views.decorators.cache import never_cache

from archive import views


urlpatterns = [
    path("api/medications/", include("medications.urls")),
    path("api/auth/", include("accounts.urls")),
    path("api/areas/", never_cache(views.AreaList.as_view())),
    path("api/areas/<slug:slug>/", never_cache(views.AreaDetail.as_view())),
    path("api/documents/", never_cache(views.DocumentList.as_view())),
    path("api/documents/suggestions/", never_cache(views.suggestions)),
    path("api/documents/bulk-delete/", never_cache(views.bulk_delete)),
    path("api/documents/<uuid:pk>/", never_cache(views.DocumentDetail.as_view())),
    path("api/documents/<uuid:pk>/file/", never_cache(views.original), name="original"),
]
