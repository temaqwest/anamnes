from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .area_suggestions import suggest_areas
from .deletion import delete_documents
from .filenames import suggest_metadata
from .models import Document
from .search import search_documents
from .serializers import (
    AreaSerializer, DocumentDeletionSerializer, DocumentEditSerializer, DocumentQuerySerializer,
    DocumentSerializer, FilenameBatchSerializer,
)
from .study_areas import areas_for


class OwnedAreas:
    serializer_class = AreaSerializer

    def get_queryset(self):
        return areas_for(self.request.user)


class AreaList(OwnedAreas, generics.ListCreateAPIView):
    pass


class AreaDetail(OwnedAreas, generics.UpdateAPIView):
    lookup_field = "slug"
    http_method_names = ["patch", "options"]


@api_view(["POST"])
def suggestions(request):
    batch = FilenameBatchSerializer(data=request.data)
    batch.is_valid(raise_exception=True)
    personal_slugs = dict(areas_for(request.user).exclude(preset=None).values_list("preset_id", "slug"))
    results = []
    for name in batch.validated_data["names"]:
        metadata = suggest_metadata(name)
        results.append({**metadata, "area_suggestions": suggest_areas(metadata["title"] or "", personal_slugs)})
    return Response(results)


class OwnedDocuments:
    def get_queryset(self):
        return Document.objects.filter(owner=self.request.user).prefetch_related("areas")


class DocumentList(OwnedDocuments, generics.ListCreateAPIView):
    serializer_class = DocumentSerializer

    def get_queryset(self):
        documents = super().get_queryset()
        if area := self.request.query_params.get("area"):
            documents = documents.filter(areas__slug=area)
        return documents

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def filter_queryset(self, queryset):
        documents = super().filter_queryset(queryset)
        filters = DocumentQuerySerializer(data=self.request.query_params)
        filters.is_valid(raise_exception=True)
        if category := filters.validated_data["category"]:
            documents = documents.filter(category="" if category == "uncategorized" else category)
        return search_documents(documents, filters.validated_data["q"])


class DocumentDetail(OwnedDocuments, generics.RetrieveUpdateAPIView):
    serializer_class = DocumentEditSerializer
    http_method_names = ["get", "patch", "head", "options"]


@api_view(["POST"])
def bulk_delete(request):
    selection = DocumentDeletionSerializer(data=request.data)
    selection.is_valid(raise_exception=True)
    return Response({"deleted": delete_documents(request.user, selection.validated_data.get("ids"))})


@api_view(["GET"])
def original(request, pk):
    document = get_object_or_404(Document, pk=pk, owner=request.user)
    try:
        stream = document.original.open("rb")
    except FileNotFoundError as error:
        raise Http404 from error
    return FileResponse(stream, content_type="application/pdf", filename=document.original_name)
