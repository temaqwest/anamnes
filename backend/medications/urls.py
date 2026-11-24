from django.urls import path
from django.views.decorators.cache import never_cache

from .views import MedicationArchive, MedicationList


urlpatterns = [
    path("", never_cache(MedicationList.as_view())),
    path("<uuid:pk>/archive/", never_cache(MedicationArchive.as_view())),
]
