from django.contrib import admin
from cruise_app.models import Person, CrewImage

class CrewImageInline(admin.TabularInline):
    model = CrewImage
    extra = 1
    fields = ('image_type', 'image', 'uploaded_at')
    readonly_fields = ('uploaded_at',)

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'crew_id_number', 'nationality', 'position')
    search_fields = ('full_name', 'crew_id_number')
    inlines = [CrewImageInline]

@admin.register(CrewImage)
class CrewImageAdmin(admin.ModelAdmin):
    list_display = ('person', 'image_type', 'uploaded_at')
    search_fields = ('person__full_name', 'person__crew_id_number')
    list_filter = ('image_type',)