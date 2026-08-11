import type { FC } from 'react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { getPower, processJarvis, setPower } from '../api/client';
import { connectJarvisSocket, type JarvisSocket } from '../api/jarvisSocket';
import { AppShell } from '../components/AppShell';
import { ConfirmModal } from '../components/ConfirmModal';
import { StatusLog } from '../components/StatusLog';

interface ConfirmState {
  requestId: string;
  title: string;
  message: string;
}

export const JarvisPage: FC = () => {
  const [enabled, setEnabled] = useState(false);
  const [listening, setListening] = useState(false);
  const [text, setText] = useState('');
  const [lines, setLines] = useState<string[]>([]);
  const [confirm, setConfirm] = useState<ConfirmState | null>(null);
  const [busy, setBusy] = useState(false);
  const socketRef = useRef<JarvisSocket | null>(null);

  const push = useCallback((message: string) => {
    setLines((prev) => [...prev, message]);
  }, []);

  useEffect(() => {
    void getPower()
      .then((state) => setEnabled(state.enabled))
      .catch((err: Error) => push(`Power sync error: ${err.message}`));

    const socket = connectJarvisSocket({
      onStatus: (message) => push(message),
      onListenState: (state) => setListening(state),
      onTranscript: (transcript) => setText(transcript),
      onResult: (message, ok) => push(`${ok ? '[OK]' : '[FAIL]'} ${message}`),
      onConfirmRequest: (requestId, title, message) => {
        setConfirm({ requestId, title, message });
      },
      onError: (message) => push(`[ERR] ${message}`),
      onOpen: () => push('[WS] linked'),
      onClose: () => push('[WS] disconnected'),
    });
    socketRef.current = socket;
    return () => {
      socket.close();
      socketRef.current = null;
    };
  }, [push]);

  async function togglePower() {
    try {
      const next = !enabled;
      const state = await setPower(next);
      setEnabled(state.enabled);
      push(`Jarvis ${state.enabled ? 'ON' : 'OFF'}`);
    } catch (err) {
      push(`Power error: ${(err as Error).message}`);
    }
  }

  async function runText() {
    const value = text.trim().toLowerCase();
    if (!enabled) {
      push('Jarvis вимкнено. Натисніть Start Jarvis.');
      return;
    }
    if (!value) {
      push('Порожній текст.');
      return;
    }
    setBusy(true);
    try {
      if (socketRef.current) {
        socketRef.current.send('jarvis.process', { text: value, execute: true });
      } else {
        const result = await processJarvis(value, true);
        result.status.forEach((line) => push(line));
        result.results.forEach((item) => push(`${item.ok ? '[OK]' : '[FAIL]'} ${item.message}`));
      }
    } catch (err) {
      push(`Process error: ${(err as Error).message}`);
    } finally {
      setBusy(false);
    }
  }

  function toggleMic() {
    const socket = socketRef.current;
    if (!socket) {
      push('WebSocket недоступний');
      return;
    }
    if (listening) {
      socket.send('listen.stop');
      return;
    }
    socket.send('listen.start');
  }

  function respondConfirm(accepted: boolean) {
    if (!confirm) {
      return;
    }
    socketRef.current?.send('confirm.response', {
      request_id: confirm.requestId,
      accepted,
    });
    setConfirm(null);
  }

  return (
    <AppShell title="Voice / text command uplink">
      <div className="max-w-4xl space-y-4">
        <div className="flex flex-wrap gap-3 items-center">
          <button
            type="button"
            className={`riat-btn ${enabled ? 'border-riat-ok text-riat-ok' : ''}`}
            onClick={() => void togglePower()}
          >
            Start Jarvis: {enabled ? 'ON' : 'OFF'}
          </button>
          <button
            type="button"
            className={`riat-btn ${listening ? 'listening-pulse border-riat-fg' : ''}`}
            onClick={toggleMic}
          >
            {listening ? 'Зупинити мікрофон' : 'Ввімкнути мікрофон'}
          </button>
        </div>

        <StatusLog lines={lines} />

        <div className="flex flex-col sm:flex-row gap-3">
          <input
            className="riat-input"
            value={text}
            onChange={(event) => setText(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                void runText();
              }
            }}
            placeholder="атас котра година"
          />
          <button
            type="button"
            className="riat-btn whitespace-nowrap"
            disabled={busy}
            onClick={() => void runText()}
          >
            Зчитати
          </button>
        </div>
      </div>

      <ConfirmModal
        open={confirm !== null}
        title={confirm?.title ?? ''}
        message={confirm?.message ?? ''}
        onAccept={() => respondConfirm(true)}
        onDecline={() => respondConfirm(false)}
      />
    </AppShell>
  );
};
