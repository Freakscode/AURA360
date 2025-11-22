import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';
import { BodyMeasurement, CreateBodyMeasurementDTO } from '../../../core/models/body-measurement.interface';

@Injectable({
  providedIn: 'root'
})
export class BodyMeasurementService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiBaseUrl}/body/measurements`;

  /**
   * Obtiene el historial de medidas de un paciente específico.
   * @param userId ID del paciente (auth_user_id)
   */
  getMeasurementsByPatient(userId: string): Observable<BodyMeasurement[]> {
    let params = new HttpParams().set('user_id', userId);
    return this.http.get<any>(this.apiUrl + '/', { params }).pipe(
      map(response => {
        if (response && response.results && Array.isArray(response.results)) {
          return response.results;
        }
        return Array.isArray(response) ? response : [];
      })
    );
  }

  /**
   * Registra una nueva medición para un paciente.
   */
  createMeasurement(measurement: CreateBodyMeasurementDTO): Observable<BodyMeasurement> {
    return this.http.post<BodyMeasurement>(this.apiUrl + '/', measurement);
  }

  /**
   * Actualiza una medición existente.
   */
  updateMeasurement(id: string, changes: Partial<BodyMeasurement>): Observable<BodyMeasurement> {
    return this.http.patch<BodyMeasurement>(`${this.apiUrl}/${id}/`, changes);
  }

  /**
   * Elimina una medición.
   */
  deleteMeasurement(id: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}/`);
  }
}
