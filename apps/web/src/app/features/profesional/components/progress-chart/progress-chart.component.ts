import { Component, computed, input } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface ChartPoint {
  date: string;
  value: number;
  label: string;
}

@Component({
  selector: 'app-progress-chart',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="chart-container">
      <svg [attr.viewBox]="'0 0 ' + width + ' ' + height" class="chart-svg">
        <!-- Grid Lines (Horizontal) -->
        @for (line of gridLines(); track $index) {
          <line
            [attr.x1]="padding"
            [attr.y1]="line.y"
            [attr.x2]="width - padding"
            [attr.y2]="line.y"
            stroke="#e5e7eb"
            stroke-width="1"
          />
          <text
            [attr.x]="padding - 10"
            [attr.y]="line.y + 4"
            text-anchor="end"
            class="axis-label"
          >
            {{ line.value }}
          </text>
        }

        <!-- Data Path -->
        <path
          [attr.d]="pathD()"
          fill="none"
          [attr.stroke]="color()"
          stroke-width="3"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
        
        <!-- Fill Area (Gradient) -->
        <path
          [attr.d]="areaD()"
          [attr.fill]="fillColor()"
          opacity="0.2"
        />

        <!-- Data Points -->
        @for (point of points(); track point.original.date) {
          <circle
            [attr.cx]="point.x"
            [attr.cy]="point.y"
            r="4"
            fill="white"
            [attr.stroke]="color()"
            stroke-width="2"
            class="point-circle"
          >
            <title>{{ point.original.label }}: {{ point.original.value }}</title>
          </circle>
        }
        
        <!-- X Axis Labels -->
        @for (point of points(); track point.original.date) {
           <text
             [attr.x]="point.x"
             [attr.y]="height - 5"
             text-anchor="middle"
             class="axis-label"
           >
             {{ formatDate(point.original.date) }}
           </text>
        }
      </svg>
    </div>
  `,
  styles: [`
    .chart-container {
      width: 100%;
      height: 300px;
      font-family: 'Inter', sans-serif;
    }
    .chart-svg {
      width: 100%;
      height: 100%;
    }
    .axis-label {
      font-size: 10px;
      fill: #6b7280;
    }
    .point-circle {
      transition: r 0.2s;
      cursor: pointer;
    }
    .point-circle:hover {
      r: 6;
    }
  `]
})
export class ProgressChartComponent {
  data = input.required<ChartPoint[]>();
  color = input<string>('#0ea5e9'); // Sky 500 default
  
  // SVG Dimensions
  width = 600;
  height = 300;
  padding = 40;

  fillColor = computed(() => this.color());

  // Processed Data Points
  points = computed(() => {
    const rawData = this.data();
    if (rawData.length === 0) return [];

    // Sort by date
    const sorted = [...rawData].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

    // Find Ranges
    const values = sorted.map(d => d.value);
    const minVal = Math.min(...values) * 0.95; // 5% buffer
    const maxVal = Math.max(...values) * 1.05;
    const range = maxVal - minVal || 1; // Avoid division by zero

    const stepX = (this.width - (this.padding * 2)) / (sorted.length - 1 || 1);

    return sorted.map((d, index) => {
      const x = this.padding + (index * stepX);
      // Y axis is inverted in SVG (0 is top)
      const normalizedValue = (d.value - minVal) / range;
      const y = (this.height - this.padding) - (normalizedValue * (this.height - (this.padding * 2)));
      return { x, y, original: d };
    });
  });

  pathD = computed(() => {
    const pts = this.points();
    if (pts.length === 0) return '';
    return `M ${pts.map(p => `${p.x},${p.y}`).join(' L ')}`;
  });
  
  areaD = computed(() => {
     const pts = this.points();
     if (pts.length === 0) return '';
     const linePath = `M ${pts.map(p => `${p.x},${p.y}`).join(' L ')}`;
     const bottomY = this.height - this.padding;
     return `${linePath} L ${pts[pts.length - 1].x},${bottomY} L ${pts[0].x},${bottomY} Z`;
  });

  gridLines = computed(() => {
     // Simple grid: 5 lines
     const lines = [];
     for (let i = 0; i <= 4; i++) {
        const y = this.padding + (i * (this.height - 2 * this.padding) / 4);
        // Calculate value at this Y (inverse of mapping)
        // This is rough for visualization only
        // Better to use min/max from data
        const rawData = this.data();
        if (rawData.length === 0) break;
        const values = rawData.map(d => d.value);
        const minVal = Math.min(...values) * 0.95;
        const maxVal = Math.max(...values) * 1.05;
        const range = maxVal - minVal || 1;
        
        // normalized 0 at bottom (height-padding), 1 at top (padding)
        const normalizedY = 1 - ((y - this.padding) / (this.height - 2 * this.padding));
        const value = minVal + (normalizedY * range);
        
        lines.push({ y, value: value.toFixed(1) });
     }
     return lines;
  });

  formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    return `${date.getDate()}/${date.getMonth() + 1}`;
  }
}