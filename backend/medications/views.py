from django.utils import timezone
from rest_framework import generics
from rest_framework.response import Response

from .models import Medication
from .serializers import MedicationArchiveSerializer, MedicationSerializer


class OwnedMedications:
    def get_queryset(self):
        return Medication.objects.filter(owner=self.request.user)


class MedicationList(OwnedMedications, generics.ListCreateAPIView):
    serializer_class = MedicationSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class MedicationArchive(OwnedMedications, generics.GenericAPIView):
    serializer_class = MedicationArchiveSerializer

    def post(self, request, pk):
        medication = self.get_object()
        if medication.archived_at is None:
            serializer = self.get_serializer(medication, data=request.data)
            serializer.is_valid(raise_exception=True)
            self.get_queryset().filter(pk=pk, archived_at__isnull=True).update(
                archived_at=timezone.now(), end_date=serializer.validated_data.get("end_date"),
            )
            medication = self.get_object()
        return Response(MedicationSerializer(medication).data)
