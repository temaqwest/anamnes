from rest_framework import generics

from .models import Allergy
from .serializers import AllergySerializer


class AllergyList(generics.ListCreateAPIView):
    serializer_class = AllergySerializer

    def get_queryset(self):
        return Allergy.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
