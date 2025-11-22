import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatDividerModule } from '@angular/material/divider';

interface Message {
  id: string;
  text: string;
  sender: 'me' | 'other';
  time: string;
}

interface Conversation {
  id: string;
  name: string;
  lastMessage: string;
  time: string;
  unread: number;
  active?: boolean;
}

@Component({
  selector: 'app-mensajes',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatListModule,
    MatIconModule,
    MatButtonModule,
    MatInputModule,
    MatFormFieldModule,
    MatDividerModule
  ],
  template: `
    <div class="inbox-container">
      <!-- Sidebar: Conversation List -->
      <div class="inbox-sidebar">
        <div class="sidebar-header">
          <h2>Mensajes</h2>
          <button mat-icon-button color="primary">
            <mat-icon>edit_square</mat-icon>
          </button>
        </div>
        
        <div class="search-bar">
           <input type="text" placeholder="Buscar conversación...">
           <mat-icon>search</mat-icon>
        </div>

        <div class="conversation-list">
          @for (conv of conversations(); track conv.id) {
            <div 
              class="conversation-item" 
              [class.active]="conv.active"
              (click)="selectConversation(conv.id)"
            >
              <div class="avatar">{{ conv.name.charAt(0) }}</div>
              <div class="conv-content">
                <div class="conv-top">
                  <span class="conv-name">{{ conv.name }}</span>
                  <span class="conv-time">{{ conv.time }}</span>
                </div>
                <div class="conv-bottom">
                  <span class="conv-msg">{{ conv.lastMessage }}</span>
                  @if (conv.unread > 0) {
                    <span class="unread-badge">{{ conv.unread }}</span>
                  }
                </div>
              </div>
            </div>
          }
        </div>
      </div>

      <!-- Main: Chat Area -->
      <div class="chat-area">
        @if (activeConversationId()) {
          <div class="chat-header">
            <div class="header-user">
              <div class="avatar-sm">M</div>
              <div class="user-details">
                <span class="username">María González</span>
                <span class="status">En línea</span>
              </div>
            </div>
            <div class="header-actions">
              <button mat-icon-button><mat-icon>phone</mat-icon></button>
              <button mat-icon-button><mat-icon>videocam</mat-icon></button>
              <button mat-icon-button><mat-icon>more_vert</mat-icon></button>
            </div>
          </div>

          <div class="messages-container">
            @for (msg of messages(); track msg.id) {
              <div class="message-wrapper" [class.me]="msg.sender === 'me'">
                <div class="message-bubble">
                  {{ msg.text }}
                </div>
                <div class="message-time">{{ msg.time }}</div>
              </div>
            }
          </div>

          <div class="chat-input-area">
            <button mat-icon-button class="attach-btn"><mat-icon>attach_file</mat-icon></button>
            <input type="text" placeholder="Escribe un mensaje..." class="message-input">
            <button mat-icon-button color="primary" class="send-btn">
              <mat-icon>send</mat-icon>
            </button>
          </div>
        } @else {
          <div class="empty-state">
            <mat-icon class="empty-icon">chat_bubble_outline</mat-icon>
            <h3>Selecciona una conversación</h3>
            <p>Elige un contacto de la izquierda para comenzar a chatear.</p>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    .inbox-container {
      display: flex;
      height: calc(100vh - 140px); // Adjust based on header/padding
      background: white;
      border-radius: 16px;
      border: 1px solid #e2e8f0;
      overflow: hidden;
    }

    // Sidebar
    .inbox-sidebar {
      width: 320px;
      border-right: 1px solid #e2e8f0;
      display: flex;
      flex-direction: column;
      background: #f8fafc;
    }

    .sidebar-header {
      padding: 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      h2 { margin: 0; font-size: 1.25rem; }
    }

    .search-bar {
      margin: 0 16px 16px;
      position: relative;
      
      input {
        width: 100%;
        padding: 10px 12px 10px 36px;
        border-radius: 8px;
        border: 1px solid #cbd5e1;
        background: white;
        
        &:focus { outline: none; border-color: #ac4fc6; }
      }
      
      mat-icon {
        position: absolute;
        left: 8px;
        top: 50%;
        transform: translateY(-50%);
        color: #94a3b8;
        font-size: 20px;
      }
    }

    .conversation-list {
      flex: 1;
      overflow-y: auto;
    }

    .conversation-item {
      padding: 12px 16px;
      display: flex;
      gap: 12px;
      cursor: pointer;
      transition: background 0.2s;
      
      &:hover { background: #f1f5f9; }
      &.active { background: #fff; border-left: 3px solid #ac4fc6; }
      
      .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: #e2e8f0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        flex-shrink: 0;
      }
      
      .conv-content {
        flex: 1;
        min-width: 0;
        
        .conv-top {
          display: flex;
          justify-content: space-between;
          margin-bottom: 4px;
          
          .conv-name { font-weight: 600; font-size: 0.9rem; }
          .conv-time { font-size: 0.75rem; color: #94a3b8; }
        }
        
        .conv-bottom {
          display: flex;
          justify-content: space-between;
          align-items: center;
          
          .conv-msg {
            font-size: 0.85rem;
            color: #64748b;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }
          
          .unread-badge {
            background: #ef4444;
            color: white;
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 10px;
            min-width: 18px;
            text-align: center;
          }
        }
      }
    }

    // Chat Area
    .chat-area {
      flex: 1;
      display: flex;
      flex-direction: column;
      background: #fff;
    }

    .chat-header {
      padding: 16px;
      border-bottom: 1px solid #e2e8f0;
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .header-user {
        display: flex;
        align-items: center;
        gap: 12px;
        
        .avatar-sm {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          background: #dbeafe;
          color: #1e40af;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 600;
        }
        
        .user-details {
          display: flex;
          flex-direction: column;
          
          .username { font-weight: 600; font-size: 0.95rem; }
          .status { font-size: 0.75rem; color: #16a34a; }
        }
      }
      
      .header-actions { color: #64748b; }
    }

    .messages-container {
      flex: 1;
      padding: 20px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .message-wrapper {
      max-width: 70%;
      align-self: flex-start;
      
      &.me {
        align-self: flex-end;
        
        .message-bubble {
          background: #ac4fc6;
          color: white;
          border-bottom-right-radius: 2px;
          border-bottom-left-radius: 12px;
        }
        
        .message-time { text-align: right; }
      }
      
      .message-bubble {
        padding: 12px 16px;
        background: #f1f5f9;
        color: #1e293b;
        border-radius: 12px;
        border-bottom-left-radius: 2px;
        font-size: 0.95rem;
        line-height: 1.4;
      }
      
      .message-time {
        font-size: 0.7rem;
        color: #94a3b8;
        margin-top: 4px;
      }
    }

    .chat-input-area {
      padding: 16px;
      border-top: 1px solid #e2e8f0;
      display: flex;
      align-items: center;
      gap: 12px;
      
      .attach-btn { color: #94a3b8; }
      
      .message-input {
        flex: 1;
        border: 1px solid #e2e8f0;
        border-radius: 24px;
        padding: 10px 16px;
        font-size: 0.95rem;
        
        &:focus { outline: none; border-color: #ac4fc6; }
      }
    }

    .empty-state {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      color: #94a3b8;
      
      .empty-icon { font-size: 64px; width: 64px; height: 64px; margin-bottom: 16px; opacity: 0.5; }
      h3 { color: #475569; margin-bottom: 8px; }
    }
  `]
})
export class MensajesComponent {
  activeConversationId = signal<string | null>('1');

  conversations = signal<Conversation[]>([
    {
      id: '1',
      name: 'María González',
      lastMessage: 'Gracias doctora, nos vemos mañana.',
      time: '10:30 AM',
      unread: 0,
      active: true
    },
    {
      id: '2',
      name: 'Carlos Rodríguez',
      lastMessage: '¿Podría cambiar mi cita?',
      time: 'Ayer',
      unread: 2,
      active: false
    }
  ]);

  messages = signal<Message[]>([
    { id: '1', text: 'Hola María, ¿cómo te has sentido con el medicamento?', sender: 'me', time: '10:15 AM' },
    { id: '2', text: 'Mucho mejor, doctora. Ya no tengo mareos.', sender: 'other', time: '10:20 AM' },
    { id: '3', text: 'Me alegro mucho. Mantén la dosis actual.', sender: 'me', time: '10:22 AM' },
    { id: '4', text: 'Gracias doctora, nos vemos mañana.', sender: 'other', time: '10:30 AM' }
  ]);

  selectConversation(id: string) {
    this.activeConversationId.set(id);
    this.conversations.update(list => list.map(c => ({ ...c, active: c.id === id })));
  }
}
