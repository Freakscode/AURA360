"""Admin configuration for papers app."""

from django.contrib import admin
from .models import ClinicalPaper


@admin.register(ClinicalPaper)
class ClinicalPaperAdmin(admin.ModelAdmin):
    """Admin interface for ClinicalPaper model."""

    list_display = ['title', 'journal', 'publication_year', 'uploaded_at']
    list_filter = ['publication_year', 'journal', 'uploaded_at']
    search_fields = ['title', 'authors', 'doi', 'topics']
    readonly_fields = ['doc_id', 'uploaded_at', 'updated_at']

    fieldsets = (
        ('Información Principal', {
            'fields': ('doc_id', 'title', 'authors', 'journal', 'publication_year', 'doi')
        }),
        ('Almacenamiento', {
            'fields': ('s3_key', 's3_bucket', 's3_region')
        }),
        ('Clasificación', {
            'fields': ('topics', 'keywords', 'abstract')
        }),
        ('Metadata', {
            'fields': ('uploaded_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
