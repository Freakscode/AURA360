"""Uploader de papers a cloud storage (GCS/S3)."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False

try:
    import boto3
    from botocore.exceptions import ClientError
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False

from .models import PaperEntry, UploadResult


class CloudUploader:
    """Uploader unificado para GCS y S3."""

    def __init__(
        self,
        provider: str = "gcs",
        bucket: Optional[str] = None,
        project: Optional[str] = None,
        region: Optional[str] = None,
        dry_run: bool = False,
    ):
        self.provider = provider
        self.bucket_name = bucket
        self.project = project
        self.region = region or "us-east-1"
        self.dry_run = dry_run

        if provider == "gcs":
            if not GCS_AVAILABLE:
                raise ImportError("google-cloud-storage no está instalado. Ejecuta: pip install google-cloud-storage")
            self.storage_client = storage.Client(project=project) if not dry_run else None
            self.bucket = self.storage_client.bucket(bucket) if not dry_run else None
        elif provider == "s3":
            if not S3_AVAILABLE:
                raise ImportError("boto3 no está instalado. Ejecuta: pip install boto3")
            self.s3_client = boto3.client("s3", region_name=region) if not dry_run else None
        else:
            raise ValueError(f"Provider no soportado: {provider}. Usa 'gcs' o 's3'")

    def upload_papers(self, papers: List[PaperEntry]) -> List[UploadResult]:
        """Sube batch de papers a cloud storage."""
        print(f"\n{'━' * 60}")
        print(f"FASE 2: UPLOAD A {self.provider.upper()}")
        print(f"{'━' * 60}\n")

        if self.dry_run:
            print("🔍 Modo DRY RUN: No se subirán archivos reales\n")

        results = []
        success_count = 0
        total = len(papers)

        for i, paper in enumerate(papers, 1):
            result = self._upload_single_paper(paper, i, total)
            results.append(result)

            if result.success:
                success_count += 1
                paper.status = "uploaded"
                paper.upload_timestamp = datetime.now()

                if self.provider == "gcs":
                    paper.gcs_uri = result.cloud_uri
                else:
                    paper.s3_uri = result.cloud_uri

            # Progress indicator
            self._print_progress(i, total, success_count)

        print(f"\n✅ {success_count}/{total} papers subidos exitosamente")
        if total - success_count > 0:
            print(f"❌ {total - success_count} fallos\n")

        return results

    def _upload_single_paper(self, paper: PaperEntry, current: int, total: int) -> UploadResult:
        """Sube un paper individual con su metadata."""
        try:
            if not paper.local_path or not paper.local_path.exists():
                return UploadResult(
                    doc_id=paper.doc_id,
                    success=False,
                    error_message=f"Archivo local no encontrado: {paper.local_path}"
                )

            # Construir paths en cloud
            category = paper.category.value
            primary_topic = paper.topics[0] if paper.topics else "general"

            pdf_key = f"{category}/{primary_topic}/{paper.doc_id}.pdf"
            metadata_key = f"{category}/{primary_topic}/{paper.doc_id}.json"

            if self.dry_run:
                # Simular upload en dry run
                cloud_uri = f"{self.provider}://{self.bucket_name}/{pdf_key}"
                time.sleep(0.1)  # Simular latencia
                return UploadResult(
                    doc_id=paper.doc_id,
                    success=True,
                    cloud_uri=cloud_uri
                )

            # Upload real según provider
            if self.provider == "gcs":
                cloud_uri = self._upload_to_gcs(paper, pdf_key, metadata_key)
            else:
                cloud_uri = self._upload_to_s3(paper, pdf_key, metadata_key)

            return UploadResult(
                doc_id=paper.doc_id,
                success=True,
                cloud_uri=cloud_uri
            )

        except Exception as e:
            error_msg = f"Error subiendo {paper.filename}: {str(e)}"
            print(f"\n❌ {error_msg}")
            return UploadResult(
                doc_id=paper.doc_id,
                success=False,
                error_message=error_msg
            )

    def _upload_to_gcs(self, paper: PaperEntry, pdf_key: str, metadata_key: str) -> str:
        """Sube a Google Cloud Storage."""
        # Upload PDF
        blob_pdf = self.bucket.blob(pdf_key)
        blob_pdf.upload_from_filename(str(paper.local_path))

        # Upload metadata JSON
        metadata_dict = paper.to_dict()
        metadata_json = json.dumps(metadata_dict, indent=2, ensure_ascii=False)

        blob_metadata = self.bucket.blob(metadata_key)
        blob_metadata.upload_from_string(
            metadata_json,
            content_type="application/json"
        )

        return f"gs://{self.bucket_name}/{pdf_key}"

    def _upload_to_s3(self, paper: PaperEntry, pdf_key: str, metadata_key: str) -> str:
        """Sube a Amazon S3."""
        # Upload PDF
        self.s3_client.upload_file(
            str(paper.local_path),
            self.bucket_name,
            pdf_key
        )

        # Upload metadata JSON
        metadata_dict = paper.to_dict()
        metadata_json = json.dumps(metadata_dict, indent=2, ensure_ascii=False)

        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=metadata_key,
            Body=metadata_json.encode('utf-8'),
            ContentType="application/json"
        )

        return f"s3://{self.bucket_name}/{pdf_key}"

    def _print_progress(self, current: int, total: int, success: int) -> None:
        """Imprime barra de progreso."""
        percentage = int((current / total) * 100)
        bar_length = 40
        filled_length = int(bar_length * current // total)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)

        print(f"\r[{bar}] {current}/{total} papers ({percentage}%) | ✅ {success} exitosos", end="", flush=True)

    def verify_uploads(self, papers: List[PaperEntry]) -> dict:
        """Verifica que los archivos existan en cloud storage."""
        print("\n🔍 Verificando uploads...\n")

        verified = 0
        missing = []

        for paper in papers:
            cloud_uri = paper.cloud_uri
            if not cloud_uri:
                missing.append(paper.doc_id)
                continue

            exists = self._check_file_exists(cloud_uri)
            if exists:
                verified += 1
            else:
                missing.append(paper.doc_id)

        print(f"✅ Verificados: {verified}/{len(papers)}")
        if missing:
            print(f"❌ Faltantes: {len(missing)}")
            print(f"   {', '.join(missing[:10])}")
            if len(missing) > 10:
                print(f"   ... y {len(missing) - 10} más")

        return {
            "verified": verified,
            "missing": missing,
            "total": len(papers)
        }

    def _check_file_exists(self, uri: str) -> bool:
        """Verifica si un archivo existe en cloud storage."""
        if self.dry_run:
            return True

        try:
            if uri.startswith("gs://"):
                # GCS
                parts = uri.replace("gs://", "").split("/", 1)
                bucket_name = parts[0]
                blob_name = parts[1]
                bucket = self.storage_client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                return blob.exists()

            elif uri.startswith("s3://"):
                # S3
                parts = uri.replace("s3://", "").split("/", 1)
                bucket_name = parts[0]
                key = parts[1]
                self.s3_client.head_object(Bucket=bucket_name, Key=key)
                return True

        except Exception:
            return False

        return False
