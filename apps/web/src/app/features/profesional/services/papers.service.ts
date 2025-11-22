import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

/**
 * Modelo de artículo científico.
 */
export interface ClinicalPaper {
  doc_id: string;
  title: string;
  authors: string;
  journal: string;
  publication_year: number | null;
  doi: string;
  has_doi: boolean;
  abstract: string;
  keywords: string[];
  topics: string[];
  uploaded_at: string;
  s3_key: string;
  s3_bucket: string;
  s3_region: string;
  s3_url: string;
  file_size_bytes: number | null;
  is_public: boolean;
  metadata: Record<string, any>;
}

/**
 * Respuesta de presigned URL para descargar paper.
 */
export interface PaperDownloadResponse {
  url: string;
  title: string;
  expires_in: number;
  doc_id: string;
  file_size_bytes: number | null;
}

/**
 * Servicio para gestionar artículos científicos almacenados en S3.
 */
@Injectable({
  providedIn: 'root'
})
export class PapersService {
  private readonly apiUrl = `${environment.apiUrl}/papers`;

  constructor(private http: HttpClient) {}

  /**
   * Obtener lista de papers científicos.
   *
   * @param filters Filtros opcionales (topic, year, journal)
   * @returns Observable con lista de papers
   */
  getPapers(filters?: {
    topic?: string[];
    year?: number;
    journal?: string;
  }): Observable<ClinicalPaper[]> {
    let params = new HttpParams();

    if (filters?.topic) {
      filters.topic.forEach(t => {
        params = params.append('topic', t);
      });
    }

    if (filters?.year) {
      params = params.set('year', filters.year.toString());
    }

    if (filters?.journal) {
      params = params.set('journal', filters.journal);
    }

    return this.http.get<ClinicalPaper[]>(this.apiUrl, { params });
  }

  /**
   * Obtener detalle de un paper específico.
   *
   * @param docId UUID del documento
   * @returns Observable con el paper
   */
  getPaper(docId: string): Observable<ClinicalPaper> {
    return this.http.get<ClinicalPaper>(`${this.apiUrl}/${docId}/`);
  }

  /**
   * Obtener presigned URL para descargar el PDF del paper.
   *
   * @param docId UUID del documento
   * @returns Observable con la URL presignada
   */
  getDownloadUrl(docId: string): Observable<PaperDownloadResponse> {
    return this.http.get<PaperDownloadResponse>(
      `${this.apiUrl}/${docId}/download/`
    );
  }

  /**
   * Abre el PDF del paper en una nueva pestaña.
   *
   * @param docId UUID del documento
   */
  openPaper(docId: string): void {
    this.getDownloadUrl(docId).subscribe({
      next: (response) => {
        window.open(response.url, '_blank');
      },
      error: (err) => {
        console.error('Error abriendo artículo:', err);
        // TODO: Mostrar notificación de error al usuario
      }
    });
  }

  /**
   * Descarga el PDF del paper.
   *
   * @param docId UUID del documento
   */
  downloadPaper(docId: string): void {
    this.getDownloadUrl(docId).subscribe({
      next: (response) => {
        // Crear un link temporal para forzar descarga
        const link = document.createElement('a');
        link.href = response.url;
        link.download = `${response.title}.pdf`;
        link.target = '_blank';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      },
      error: (err) => {
        console.error('Error descargando artículo:', err);
        // TODO: Mostrar notificación de error al usuario
      }
    });
  }

  /**
   * Busca papers por topics específicos.
   *
   * @param topics Lista de topics
   * @returns Observable con papers filtrados
   */
  searchByTopics(topics: string[]): Observable<ClinicalPaper[]> {
    return this.getPapers({ topic: topics });
  }

  /**
   * Formatea el tamaño del archivo a formato legible.
   *
   * @param bytes Tamaño en bytes
   * @returns String formateado (ej. "2.5 MB")
   */
  formatFileSize(bytes: number | null): string {
    if (!bytes) return 'N/A';

    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';

    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    const size = (bytes / Math.pow(1024, i)).toFixed(2);

    return `${size} ${sizes[i]}`;
  }

  /**
   * Formatea la lista de autores para visualización.
   *
   * @param authors String de autores
   * @param maxLength Longitud máxima antes de truncar
   * @returns String formateado
   */
  formatAuthors(authors: string, maxLength: number = 50): string {
    if (!authors) return 'N/A';

    if (authors.length <= maxLength) {
      return authors;
    }

    return authors.substring(0, maxLength) + '...';
  }

  /**
   * Obtiene el emoji para un topic específico.
   *
   * @param topic Nombre del topic
   * @returns Emoji representativo
   */
  getTopicEmoji(topic: string): string {
    const topicEmojis: Record<string, string> = {
      'cardiology': '❤️',
      'nutrition': '🥗',
      'diabetes': '🩺',
      'obesity': '⚖️',
      'exercise': '🏃',
      'sleep': '😴',
      'mental_health': '🧠',
      'gut_microbiome': '🦠',
      'chrononutrition': '⏰',
      'metabolism': '🔥',
    };

    return topicEmojis[topic] || '📄';
  }
}
