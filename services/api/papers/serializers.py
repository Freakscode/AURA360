"""Serializers for papers app."""

from rest_framework import serializers
from .models import ClinicalPaper


class ClinicalPaperSerializer(serializers.ModelSerializer):
    """Serializer for ClinicalPaper model."""

    s3_url = serializers.SerializerMethodField()
    has_doi = serializers.SerializerMethodField()
    quality_badge = serializers.SerializerMethodField()

    class Meta:
        model = ClinicalPaper
        fields = [
            'doc_id',
            'title',
            'authors',
            'journal',
            'publication_year',
            'doi',
            'has_doi',
            'abstract',
            'keywords',
            's3_key',
            's3_bucket',
            's3_region',
            's3_url',
            'file_size_bytes',
            'topics',
            # Quality Assessment
            'evidence_level',
            'quality_score',
            'reliability_score',
            'clinical_relevance',
            'study_type',
            'sample_size',
            'impact_factor',
            'key_findings',
            'limitations',
            'composite_score',
            'quality_badge',
            # Management
            'uploaded_at',
            'updated_at',
            'uploaded_by',
            'is_public',
            'metadata',
        ]
        read_only_fields = [
            'doc_id',
            'uploaded_at',
            'updated_at',
            's3_url',
            'has_doi',
            'composite_score',
            'quality_badge',
        ]

    def get_s3_url(self, obj):
        """Get the base S3 URL."""
        return obj.get_s3_url()

    def get_has_doi(self, obj):
        """Check if paper has DOI."""
        return obj.has_doi()

    def get_quality_badge(self, obj):
        """Get quality badge emoji."""
        return obj.get_quality_badge()


class ClinicalPaperListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing papers."""

    has_doi = serializers.SerializerMethodField()
    quality_badge = serializers.SerializerMethodField()

    class Meta:
        model = ClinicalPaper
        fields = [
            'doc_id',
            'title',
            'authors',
            'journal',
            'publication_year',
            'doi',
            'has_doi',
            'topics',
            'study_type',
            'composite_score',
            'quality_badge',
            'uploaded_at',
        ]
        read_only_fields = fields

    def get_has_doi(self, obj):
        """Check if paper has DOI."""
        return obj.has_doi()

    def get_quality_badge(self, obj):
        """Get quality badge emoji."""
        return obj.get_quality_badge()


class PaperDownloadSerializer(serializers.Serializer):
    """Serializer for presigned URL response."""

    url = serializers.URLField(
        help_text="Presigned S3 URL for downloading the paper."
    )
    title = serializers.CharField(
        help_text="Title of the paper."
    )
    expires_in = serializers.IntegerField(
        help_text="URL expiration time in seconds."
    )
    doc_id = serializers.UUIDField(
        help_text="Document ID."
    )
    file_size_bytes = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="File size in bytes."
    )
