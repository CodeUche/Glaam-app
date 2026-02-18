import { io, Socket } from 'socket.io-client';
import { getStoredTokens } from './api';
import { Booking, Notification } from '../types';

const WS_URL = process.env.WS_URL || 'ws://localhost:8000/ws';

type BookingUpdateHandler = (booking: Booking) => void;
type NotificationHandler = (notification: Notification) => void;
type ConnectionHandler = (connected: boolean) => void;

class WebSocketManager {
  private socket: Socket | null = null;
  private bookingHandlers: Set<BookingUpdateHandler> = new Set();
  private notificationHandlers: Set<NotificationHandler> = new Set();
  private connectionHandlers: Set<ConnectionHandler> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;

  async connect(): Promise<void> {
    if (this.socket?.connected) {
      return;
    }

    const tokens = await getStoredTokens();
    if (!tokens?.access) {
      console.warn('WebSocket: No auth token available, skipping connection.');
      return;
    }

    this.socket = io(WS_URL, {
      auth: { token: tokens.access },
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 30000,
    });

    this.setupListeners();
  }

  private setupListeners(): void {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.connectionHandlers.forEach((handler) => handler(true));
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      this.connectionHandlers.forEach((handler) => handler(false));
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error.message);
      this.reconnectAttempts++;
    });

    // Booking real-time updates
    this.socket.on('booking:updated', (data: Booking) => {
      this.bookingHandlers.forEach((handler) => handler(data));
    });

    this.socket.on('booking:new', (data: Booking) => {
      this.bookingHandlers.forEach((handler) => handler(data));
    });

    this.socket.on('booking:status_changed', (data: Booking) => {
      this.bookingHandlers.forEach((handler) => handler(data));
    });

    // Notification updates
    this.socket.on('notification', (data: Notification) => {
      this.notificationHandlers.forEach((handler) => handler(data));
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.removeAllListeners();
      this.socket.disconnect();
      this.socket = null;
    }
    this.reconnectAttempts = 0;
  }

  // ---------- Subscription API ----------

  onBookingUpdate(handler: BookingUpdateHandler): () => void {
    this.bookingHandlers.add(handler);
    return () => {
      this.bookingHandlers.delete(handler);
    };
  }

  onNotification(handler: NotificationHandler): () => void {
    this.notificationHandlers.add(handler);
    return () => {
      this.notificationHandlers.delete(handler);
    };
  }

  onConnectionChange(handler: ConnectionHandler): () => void {
    this.connectionHandlers.add(handler);
    return () => {
      this.connectionHandlers.delete(handler);
    };
  }

  // ---------- Emit events ----------

  joinBookingRoom(bookingId: number): void {
    this.socket?.emit('booking:join', { bookingId });
  }

  leaveBookingRoom(bookingId: number): void {
    this.socket?.emit('booking:leave', { bookingId });
  }

  get isConnected(): boolean {
    return this.socket?.connected ?? false;
  }
}

// Singleton instance
export const wsManager = new WebSocketManager();
