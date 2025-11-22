#!/usr/bin/env python
from __future__ import annotations
"""
Script para carga masiva de papers científicos a S3 + PostgreSQL.

Uso:
    python batch_upload_papers.py /path/to/pdfs/folder

Proceso:
    1. Escanea carpeta de PDFs
    2. Analiza cada PDF con Gemini (calidad)
    3. Sube archivo a S3
    4. Crea registro en PostgreSQL con metadata

Configuración (vía environment variables):
    - GOOGLE_API_KEY: API key de Google
    - AWS_ACCESS_KEY_ID: AWS access key
    - AWS_SECRET_ACCESS_KEY: AWS secret key
    - AWS_S3_BUCKET_NAME: Bucket de S3
    - AWS_S3_REGION: Región de S3
    - DATABASE_URL: URL de PostgreSQL (opcional, usa Django settings)
"""

import os
import sys
import base64
import hashlib
import json
import uuid
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Agregar directorio raíz al path para imports de Django
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

# Imports después de Django setup
from papers.models import ClinicalPaper
from analyze_paper import analyze_paper

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    print("⚠️  boto3 no instalado. Instalando...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "boto3"])
    import boto3
    from botocore.exceptions import ClientError


class PaperUploader:
    """Clase para gestionar carga masiva de papers."""

    def __init__(
        self,
        s3_bucket: str,
        s3_region: str,
        aws_access_key: str,
        aws_secret_key: str,
        google_api_key: str,
        s3_prefix: str = "papers/nutrition",
    ):
        """
        Inicializa el uploader.

        Args:
            s3_bucket: Nombre del bucket S3
            s3_region: Región de S3
            aws_access_key: AWS access key
            aws_secret_key: AWS secret key
            google_api_key: Google API key para Gemini
            s3_prefix: Prefijo para keys en S3
        """
        self.s3_bucket = s3_bucket
        self.s3_region = s3_region
        self.google_api_key = google_api_key
        self.s3_prefix = s3_prefix

        # Cliente S3
        self.s3_client = boto3.client(
            's3',
            region_name=s3_region,
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
        )

        # Estadísticas
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'errors': [],
        }

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitiza un nombre de archivo para S3.

        Args:
            filename: Nombre original del archivo

        Returns:
            str: Nombre sanitizado
        """
        # Remover caracteres especiales
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        # Convertir a minúsculas
        sanitized = sanitized.lower()
        return sanitized

    def md5_file(self, pdf_path: str) -> str:
        """Calcula hash MD5 del PDF (para deduplicación e integridad)."""
        hash_md5 = hashlib.md5()
        with open(pdf_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def generate_s3_key(self, pdf_path: str, year: int | None = None, pdf_md5: str | None = None) -> str:
        """
        Genera un S3 key único para el paper.

        Args:
            pdf_path: Path al PDF
            year: Año de publicación (opcional)

        Returns:
            str: S3 key (ej. "papers/nutrition/2024/smith_diabetes.pdf")
        """
        filename = Path(pdf_path).name
        sanitized = self.sanitize_filename(filename)

        # Prefix con hash corto para evitar colisiones
        hash_short = (pdf_md5 or self.md5_file(pdf_path))[:8]

        # Organizar por año si está disponible
        if year:
            s3_key = f"{self.s3_prefix}/{year}/{hash_short}_{sanitized}"
        else:
            s3_key = f"{self.s3_prefix}/unknown_year/{hash_short}_{sanitized}"

        return s3_key

    def upload_to_s3(
        self,
        pdf_path: str,
        s3_key: str,
        extra_metadata: Dict[str, str] | None = None,
        md5_hex: str | None = None,
    ) -> Dict[str, Any]:
        """
        Sube un PDF a S3.

        Args:
            pdf_path: Path local al PDF
            s3_key: Key de S3

        Returns:
            dict: Información del upload (size, url)
        """
        try:
            # Obtener tamaño del archivo
            file_size = Path(pdf_path).stat().st_size
            md5_hex = md5_hex or self.md5_file(pdf_path)
            content_md5 = base64.b64encode(bytes.fromhex(md5_hex)).decode("utf-8")
            metadata = {
                'uploaded_by': 'batch_upload_script',
                'upload_date': datetime.now().isoformat(),
            }
            if extra_metadata:
                # S3 metadata requiere strings y <=2KB
                metadata.update({k: str(v) for k, v in extra_metadata.items() if v is not None})

            # Subir a S3
            self.s3_client.upload_file(
                pdf_path,
                self.s3_bucket,
                s3_key,
                ExtraArgs={
                    'ContentType': 'application/pdf',
                    'Metadata': metadata,
                    'ServerSideEncryption': 'AES256',
                    'ContentMD5': content_md5,
                }
            )

            s3_url = f"https://{self.s3_bucket}.s3.{self.s3_region}.amazonaws.com/{s3_key}"

            return {
                'success': True,
                'file_size_bytes': file_size,
                's3_url': s3_url,
            }

        except ClientError as e:
            raise Exception(f"Error subiendo a S3: {e}")

    def create_paper_record(
        self,
        analysis: Dict[str, Any],
        s3_key: str,
        file_size_bytes: int,
        pdf_md5: str,
    ) -> ClinicalPaper:
        """
        Crea registro en PostgreSQL.

        Args:
            analysis: Resultados del análisis de Gemini
            s3_key: Key en S3
            file_size_bytes: Tamaño del archivo

        Returns:
            ClinicalPaper: Instancia creada
        """
        paper = ClinicalPaper.objects.create(
            doc_id=uuid.uuid4(),
            # Bibliographic
            title=analysis.get('title', 'Unknown Title'),
            authors=analysis.get('authors', 'Unknown'),
            journal=analysis.get('journal', ''),
            publication_year=analysis.get('publication_year'),
            abstract=analysis.get('abstract', ''),
            keywords=analysis.get('keywords', []),
            # S3
            s3_key=s3_key,
            s3_bucket=self.s3_bucket,
            s3_region=self.s3_region,
            file_size_bytes=file_size_bytes,
            # Classification
            topics=analysis.get('topics', []),
            # Quality (auto-calculated composite_score en save())
            evidence_level=analysis.get('evidence_level'),
            quality_score=analysis.get('quality_score'),
            reliability_score=analysis.get('reliability_score'),
            clinical_relevance=analysis.get('clinical_relevance'),
            study_type=analysis.get('study_type', ''),
            sample_size=analysis.get('sample_size'),
            key_findings=analysis.get('key_findings', ''),
            limitations=analysis.get('limitations', ''),
            # Management
            is_public=True,  # Por defecto público
            metadata={
                'analyzed_by': analysis.get('_analysis_model', 'gemini-2.0-flash-exp'),
                'analysis_date': datetime.now().isoformat(),
                'original_filename': analysis.get('_pdf_name', ''),
                'pdf_md5': pdf_md5,
                'analysis_model': analysis.get('_analysis_model'),
                'analysis_prompt_version': analysis.get('_analysis_prompt_version'),
            }
        )

        return paper

    def process_paper(self, pdf_path: str) -> Dict[str, Any]:
        """
        Procesa un paper completo: analiza, sube y crea registro.

        Args:
            pdf_path: Path al PDF

        Returns:
            dict: Resultado del procesamiento
        """
        pdf_name = Path(pdf_path).name
        print(f"\n{'='*70}")
        print(f"📄 Procesando: {pdf_name}")
        print(f"{'='*70}")

        try:
            pdf_hash = self.md5_file(pdf_path)
            # 1. Verificar si ya existe (por nombre de archivo)
            existing = ClinicalPaper.objects.filter(metadata__pdf_md5=pdf_hash).first()
            if existing:
                print(f"⚠️  Ya existe en base de datos (hash match): {existing.doc_id}")
                self.stats['skipped'] += 1
                self.stats['errors'].append({'file': pdf_name, 'error': 'duplicate_md5', 'doc_id': str(existing.doc_id)})
                return {'status': 'skipped', 'reason': 'duplicate_md5', 'doc_id': str(existing.doc_id)}

            # 2. Analizar con Gemini
            print("🤖 Analizando con Gemini...")
            analysis = analyze_paper(pdf_path, self.google_api_key)

            # 3. Generar S3 key
            s3_key = self.generate_s3_key(pdf_path, analysis.get('publication_year'), pdf_hash)
            print(f"📦 S3 Key: {s3_key}")

            # 3b. Verificar colisión en S3
            try:
                self.s3_client.head_object(Bucket=self.s3_bucket, Key=s3_key)
                print("⚠️  Key ya existe en S3, se agregará sufijo único.")
                s3_key = s3_key.replace(".pdf", f"_{uuid.uuid4().hex[:6]}.pdf")
            except ClientError as e:
                if e.response.get("ResponseMetadata", {}).get("HTTPStatusCode") != 404:
                    raise

            # 4. Subir a S3
            print("☁️  Subiendo a S3...")
            upload_result = self.upload_to_s3(
                pdf_path,
                s3_key,
                extra_metadata={
                    'title': analysis.get('title', ''),
                    'year': analysis.get('publication_year'),
                    'quality_score': analysis.get('quality_score'),
                    'analysis_model': analysis.get('_analysis_model'),
                    'analysis_prompt_version': analysis.get('_analysis_prompt_version'),
                    'pdf_md5': pdf_hash,
                },
                md5_hex=pdf_hash,
            )

            # 5. Crear registro en DB
            print("💾 Creando registro en PostgreSQL...")
            paper = self.create_paper_record(
                analysis,
                s3_key,
                upload_result['file_size_bytes'],
                pdf_hash,
            )

            # 6. Éxito
            self.stats['success'] += 1
            print(f"✅ Procesado exitosamente!")
            print(f"   Doc ID: {paper.doc_id}")
            print(f"   Composite Score: {paper.composite_score}")
            print(f"   Quality Badge: {paper.get_quality_badge()}")

            return {
                'status': 'success',
                'doc_id': str(paper.doc_id),
                's3_key': s3_key,
                'composite_score': float(paper.composite_score) if paper.composite_score else None,
            }

        except Exception as e:
            self.stats['failed'] += 1
            error_msg = str(e)
            self.stats['errors'].append({
                'file': pdf_name,
                'error': error_msg,
            })
            print(f"❌ Error: {error_msg}")
            return {
                'status': 'failed',
                'error': error_msg,
            }

    def process_folder(self, folder_path: str) -> List[Dict[str, Any]]:
        """
        Procesa todos los PDFs de una carpeta.

        Args:
            folder_path: Path a la carpeta

        Returns:
            list: Resultados de cada paper
        """
        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            raise ValueError(f"La carpeta no existe: {folder_path}")

        # Buscar PDFs
        pdf_files = list(folder.glob("*.pdf")) + list(folder.glob("*.PDF"))
        self.stats['total'] = len(pdf_files)

        print(f"\n{'🚀'*35}")
        print(f"  CARGA MASIVA DE PAPERS")
        print(f"{'🚀'*35}")
        print(f"\n📁 Carpeta: {folder_path}")
        print(f"📄 PDFs encontrados: {len(pdf_files)}")
        print()

        results = []
        for i, pdf_path in enumerate(pdf_files, 1):
            print(f"\n[{i}/{len(pdf_files)}]")
            result = self.process_paper(str(pdf_path))
            results.append(result)

        return results

    def print_summary(self):
        """Imprime resumen de estadísticas."""
        print(f"\n\n{'='*70}")
        print(f"  📊 RESUMEN DE CARGA")
        print(f"{'='*70}")
        print(f"Total de PDFs: {self.stats['total']}")
        print(f"✅ Exitosos: {self.stats['success']}")
        print(f"⚠️  Omitidos: {self.stats['skipped']}")
        print(f"❌ Fallidos: {self.stats['failed']}")

        if self.stats['errors']:
            print(f"\n{'='*70}")
            print(f"  ❌ ERRORES DETALLADOS")
            print(f"{'='*70}")
            for error in self.stats['errors']:
                print(f"\n📄 {error['file']}")
                print(f"   Error: {error['error']}")

        print(f"\n{'='*70}\n")


def main():
    """Función principal."""
    if len(sys.argv) < 2:
        print("Uso: python batch_upload_papers.py <carpeta_pdfs>")
        print("\nEjemplo:")
        print("  python batch_upload_papers.py '/Users/user/Downloads/PDFs Referencias Nutrición'")
        sys.exit(1)

    folder_path = sys.argv[1]

    # Obtener configuración de environment
    google_api_key = os.getenv('GOOGLE_API_KEY')
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    s3_bucket = os.getenv('AWS_S3_BUCKET_NAME', 'aura360-clinical-papers')
    s3_region = os.getenv('AWS_S3_REGION', 'us-east-1')

    # Validar configuración
    if not google_api_key:
        print("❌ Error: GOOGLE_API_KEY no configurada")
        sys.exit(1)

    if not aws_access_key or not aws_secret_key:
        print("❌ Error: AWS credentials no configuradas")
        print("   Configura: AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY")
        sys.exit(1)

    # Crear uploader
    uploader = PaperUploader(
        s3_bucket=s3_bucket,
        s3_region=s3_region,
        aws_access_key=aws_access_key,
        aws_secret_key=aws_secret_key,
        google_api_key=google_api_key,
    )

    try:
        # Procesar carpeta
        results = uploader.process_folder(folder_path)

        # Imprimir resumen
        uploader.print_summary()

        # Guardar resultados en JSON
        output_file = Path(folder_path) / f"upload_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'stats': uploader.stats,
                'results': results,
            }, f, indent=2, ensure_ascii=False)

        print(f"📄 Resultados guardados en: {output_file}\n")

    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
