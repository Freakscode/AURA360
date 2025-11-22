"""Views for papers app."""

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ClinicalPaper
from .serializers import (
    ClinicalPaperSerializer,
    ClinicalPaperListSerializer,
    PaperDownloadSerializer,
)


class ClinicalPaperViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar artículos científicos.

    Endpoints:
    - GET /api/papers/ - Lista todos los papers públicos
    - GET /api/papers/{doc_id}/ - Detalle de un paper específico
    - GET /api/papers/{doc_id}/download/ - Obtener presigned URL
    """

    permission_classes = [IsAuthenticated]
    queryset = ClinicalPaper.objects.all()
    lookup_field = 'doc_id'

    def get_serializer_class(self):
        """Usa serializers diferentes según la acción."""
        if self.action == 'list':
            return ClinicalPaperListSerializer
        return ClinicalPaperSerializer

    def get_queryset(self):
        """
        Filtra papers según permisos del usuario.

        Por ahora solo muestra papers públicos.
        TODO: Agregar lógica para papers privados basada en CareRelationship.
        """
        queryset = ClinicalPaper.objects.filter(is_public=True)

        # Filtros opcionales
        topics = self.request.query_params.getlist('topic')
        if topics:
            # Filtra por topics (OR)
            queryset = queryset.filter(topics__overlap=topics)

        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(publication_year=year)

        journal = self.request.query_params.get('journal')
        if journal:
            queryset = queryset.filter(journal__icontains=journal)

        return queryset

    @action(detail=True, methods=['get'])
    def download(self, request, doc_id=None):
        """
        Genera presigned URL para descargar el PDF del paper.

        Args:
            doc_id: UUID del documento

        Returns:
            {
                "url": "https://s3.amazonaws.com/...",
                "title": "Paper Title",
                "expires_in": 900,
                "doc_id": "uuid",
                "file_size_bytes": 1234567
            }
        """
        paper = self.get_object()

        # Generar presigned URL
        try:
            s3_client = boto3.client(
                's3',
                region_name=paper.s3_region,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )

            # Generar URL con 15 minutos de validez
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': paper.s3_bucket,
                    'Key': paper.s3_key,
                    'ResponseContentDisposition': f'attachment; filename="{paper.title}.pdf"',
                    'ResponseContentType': 'application/pdf',
                },
                ExpiresIn=900,  # 15 minutos
            )

            # Preparar respuesta
            response_data = {
                'url': presigned_url,
                'title': paper.title,
                'expires_in': 900,
                'doc_id': str(paper.doc_id),
                'file_size_bytes': paper.file_size_bytes,
            }

            serializer = PaperDownloadSerializer(data=response_data)
            serializer.is_valid(raise_exception=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            return Response(
                {
                    'error': 'Error generando URL de descarga',
                    'detail': f'S3 Error: {error_code}',
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            return Response(
                {'error': 'Error inesperado generando URL', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PaperDownloadView(APIView):
    """
    Vista alternativa simplificada para obtener presigned URL.

    GET /api/papers/{doc_id}/download
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, doc_id):
        """Generate presigned URL for paper download."""
        paper = get_object_or_404(ClinicalPaper, doc_id=doc_id, is_public=True)

        try:
            s3_client = boto3.client(
                's3',
                region_name=paper.s3_region,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )

            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': paper.s3_bucket,
                    'Key': paper.s3_key,
                    'ResponseContentDisposition': f'attachment; filename="{paper.title}.pdf"',
                    'ResponseContentType': 'application/pdf',
                },
                ExpiresIn=900,
            )

            response_data = {
                'url': presigned_url,
                'title': paper.title,
                'expires_in': 900,
                'doc_id': str(paper.doc_id),
                'file_size_bytes': paper.file_size_bytes,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except ClientError as e:
            return Response(
                {'error': 'Error generando URL de descarga', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
