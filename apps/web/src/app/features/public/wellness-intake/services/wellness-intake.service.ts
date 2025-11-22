import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { environment } from '../../../../../environments/environment';
import {
  CreateIntakeSubmissionRequest,
  IntakeSubmissionResponse,
} from '../models/wellness-intake.models';

function stripTrailingSlash(url: string): string {
  return url.endsWith('/') ? url.slice(0, -1) : url;
}

@Injectable({ providedIn: 'root' })
export class WellnessIntakeService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${stripTrailingSlash(environment.apiBaseUrl)}/holistic/intake-submissions`;

  createSubmission(payload: CreateIntakeSubmissionRequest) {
    return this.http.post<IntakeSubmissionResponse>(`${this.baseUrl}/`, payload);
  }

  getSubmission(id: string) {
    return this.http.get<IntakeSubmissionResponse>(`${this.baseUrl}/${id}/`);
  }

  listSubmissions(limit = 5) {
    const params = new URLSearchParams({ limit: limit.toString() });
    return this.http.get<{ count: number; results: IntakeSubmissionResponse[] }>(
      `${this.baseUrl}/?${params}`
    );
  }
}
