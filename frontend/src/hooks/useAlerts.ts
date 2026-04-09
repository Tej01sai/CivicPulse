// WebSocket hook for real-time alerts
import { useEffect, useRef, useState, useCallback } from 'react';

const WS_URL = (import.meta.env.VITE_WS_URL || 'ws://localhost:8000') + '/ws';

export interface AlertMessage {
  type: string;
  need_id?: string;
  need_type?: string;
  urgency?: string;
  district?: string;
  message?: string;
  urgency_score?: number;
  volunteer_name?: string;
  assignment_id?: string;
  client_id?: string;
}

export function useAlerts(onAlert?: (msg: AlertMessage) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [latestAlert, setLatestAlert] = useState<AlertMessage | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        // Heartbeat
        const interval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) ws.send('ping');
        }, 25000);
        (ws as any)._interval = interval;
      };

      ws.onmessage = (event) => {
        try {
          const msg: AlertMessage = JSON.parse(event.data);
          if (msg.type === 'pong' || msg.type === 'connected') return;
          setLatestAlert(msg);
          onAlert?.(msg);
        } catch { /* ignore parse errors */ }
      };

      ws.onclose = () => {
        setConnected(false);
        clearInterval((ws as any)._interval);
        // Reconnect after 3s
        reconnectTimer.current = setTimeout(connect, 3000);
      };

      ws.onerror = () => ws.close();
    } catch (e) {
      reconnectTimer.current = setTimeout(connect, 5000);
    }
  }, [onAlert]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { connected, latestAlert };
}
