export interface JarvisSocketHandlers {
  onStatus?: (message: string) => void;
  onListenState?: (listening: boolean) => void;
  onTranscript?: (text: string) => void;
  onResult?: (message: string, ok: boolean) => void;
  onConfirmRequest?: (requestId: string, title: string, message: string) => void;
  onError?: (message: string) => void;
  onOpen?: () => void;
  onClose?: () => void;
}

export interface JarvisSocket {
  send: (event: string, payload?: Record<string, unknown>) => void;
  close: () => void;
}

function wsUrl(): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/ws/jarvis`;
}

export function connectJarvisSocket(handlers: JarvisSocketHandlers): JarvisSocket {
  const socket = new WebSocket(wsUrl());

  socket.onopen = () => {
    handlers.onOpen?.();
  };

  socket.onclose = () => {
    handlers.onClose?.();
  };

  socket.onmessage = (event: MessageEvent<string>) => {
    try {
      const data = JSON.parse(event.data) as Record<string, unknown>;
      const name = String(data.event ?? '');
      if (name === 'status') {
        handlers.onStatus?.(String(data.message ?? ''));
        return;
      }
      if (name === 'listen.state') {
        handlers.onListenState?.(Boolean(data.listening));
        return;
      }
      if (name === 'transcript') {
        handlers.onTranscript?.(String(data.text ?? ''));
        return;
      }
      if (name === 'result') {
        handlers.onResult?.(String(data.message ?? ''), Boolean(data.ok));
        return;
      }
      if (name === 'confirm.request') {
        handlers.onConfirmRequest?.(
          String(data.request_id ?? ''),
          String(data.title ?? ''),
          String(data.message ?? ''),
        );
        return;
      }
      if (name === 'error') {
        handlers.onError?.(String(data.message ?? 'Unknown error'));
      }
    } catch {
      handlers.onError?.('Invalid websocket payload');
    }
  };

  return {
    send(event: string, payload: Record<string, unknown> = {}) {
      if (socket.readyState !== WebSocket.OPEN) {
        return;
      }
      socket.send(JSON.stringify({ event, ...payload }));
    },
    close() {
      socket.close();
    },
  };
}
