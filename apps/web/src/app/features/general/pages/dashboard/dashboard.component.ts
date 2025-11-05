import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-general-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="dashboard">
      <header class="dashboard__header">
        <h1>Bienvenido a AURA360</h1>
        <p class="dashboard__subtitle">
          Plataforma holística para tu bienestar integral
        </p>
      </header>

      <div class="dashboard__welcome">
        <h2>¡Comienza tu viaje hacia el bienestar!</h2>
        <p>
          AURA360 te ofrece herramientas para cuidar tu mente, cuerpo y alma de
          forma integral.
        </p>
      </div>

      <div class="dashboard__grid">
        <div class="dashboard__card">
          <h2>🧠 Mind</h2>
          <p class="dashboard__card-desc">
            Gestiona tu estado emocional y salud mental
          </p>
          <button class="dashboard__card-btn">Explorar</button>
        </div>

        <div class="dashboard__card">
          <h2>💪 Body</h2>
          <p class="dashboard__card-desc">
            Monitorea tu actividad física y nutrición
          </p>
          <button class="dashboard__card-btn">Explorar</button>
        </div>

        <div class="dashboard__card">
          <h2>🌟 Soul</h2>
          <p class="dashboard__card-desc">Desarrolla tu propósito y valores</p>
          <button class="dashboard__card-btn">Explorar</button>
        </div>
      </div>

      <div class="dashboard__upgrade">
        <h3>Actualiza a Premium</h3>
        <p>
          Accede a funcionalidades avanzadas, reportes personalizados y más.
        </p>
        <button class="dashboard__upgrade-btn">Ver Planes</button>
      </div>
    </div>
  `,
  styles: [
    `
      .dashboard {
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
      }

      .dashboard__header {
        margin-bottom: 2rem;
        text-align: center;

        h1 {
          font-size: 2.5rem;
          font-weight: 700;
          color: #111827;
          margin: 0 0 0.5rem 0;
        }
      }

      .dashboard__subtitle {
        font-size: 1.125rem;
        color: #6b7280;
        margin: 0;
      }

      .dashboard__welcome {
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 0.75rem;
        margin-bottom: 2rem;
        text-align: center;

        h2 {
          font-size: 1.5rem;
          margin: 0 0 1rem 0;
        }

        p {
          font-size: 1rem;
          margin: 0;
          opacity: 0.9;
        }
      }

      .dashboard__grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1.5rem;
        margin-bottom: 2rem;
      }

      .dashboard__card {
        padding: 2rem;
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        text-align: center;

        h2 {
          font-size: 1.5rem;
          margin: 0 0 1rem 0;
        }
      }

      .dashboard__card-desc {
        font-size: 0.875rem;
        color: #6b7280;
        margin: 0 0 1.5rem 0;
        line-height: 1.5;
      }

      .dashboard__card-btn {
        padding: 0.625rem 1.25rem;
        background: #f3f4f6;
        color: #374151;
        border: none;
        border-radius: 0.375rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;

        &:hover {
          background: #e5e7eb;
        }
      }

      .dashboard__upgrade {
        padding: 2rem;
        background: #fef3c7;
        border: 2px solid #fbbf24;
        border-radius: 0.75rem;
        text-align: center;

        h3 {
          font-size: 1.25rem;
          font-weight: 600;
          color: #92400e;
          margin: 0 0 0.5rem 0;
        }

        p {
          font-size: 0.875rem;
          color: #78350f;
          margin: 0 0 1rem 0;
        }
      }

      .dashboard__upgrade-btn {
        padding: 0.75rem 2rem;
        background: #f59e0b;
        color: white;
        border: none;
        border-radius: 0.375rem;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.2s;

        &:hover {
          background: #d97706;
        }
      }
    `,
  ],
})
export class DashboardComponent {}
