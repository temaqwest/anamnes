from django.urls import path
from django.views.decorators.cache import never_cache

from .views import AllergyList


urlpatterns = [
    path("", never_cache(AllergyList.as_view())),
]
