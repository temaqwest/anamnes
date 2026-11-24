from .models import Area, StudyArea


def normalize_area_name(name: str) -> str:
    return " ".join(name.split())


def areas_for(owner):
    areas = StudyArea.objects.filter(owner=owner)
    if not areas.exists():
        StudyArea.objects.bulk_create([
            StudyArea(
                owner=owner, preset_id=slug, slug=slug, name=name, name_key=normalize_area_name(name).casefold(),
                description=description,
            )
            for slug, name, description in Area.objects.values_list("slug", "name", "description")
        ], ignore_conflicts=True)
    return areas
