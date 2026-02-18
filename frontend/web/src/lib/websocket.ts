"use client";

import { io, Socket } from "socket.io-client";
import { getAccessToken } from "./api";
import type { Notification } from "@/types";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";

type NotificationHandler = (notification: Notification) => void;
type ConnectionHandler = (connected: boolean) => void;

class WebSocketManager {
  private socket: Socket | null = null;
  private notificationHandlers: Set<NotificationHandler> = new Set();
  private connectionHandlers: Set<ConnectionHandler> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  connect(): void {
    const token = getAccessToken();
    if (!token) return;

    if (this.socket?.connected) return;

    this.socket = io(WS_URL, {
      auth: { token },
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 10000,
    });

    this.socket.on("connect", () => {
      this.reconnectAttempts = 0;
      this.connectionHandlers.forEach((handler) => handler(true));
    });

    this.socket.on("disconnect", () => {
      this.connectionHandlers.forEach((handler) => handler(false));
    });

    this.socket.on("notification", (data: Notification) => {
      this.notificationHandlers.forEach((handler) => handler(data));
    });

    this.socket.on("booking_update", (data: Notification) => {
      this.notificationHandlers.forEach((handler) => handler(data));
    });

    this.socket.on("connect_error", () => {
      this.reconnectAttempts++;
      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        this.disconnect();
      }
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

  emit(event: string, data: unknown): void {
    if (this.socket?.connected) {
      this.socket.emit(event, data);
    }
  }

  get isConnected(): boolean {
    return this.socket?.connected ?? false;
  }
}

const wsManager = new WebSocketManager();
export default wsManager;
