import type { FC } from 'react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

type BootPhase = 'log' | 'wait1' | 'progress' | 'wait2' | 'matrix' | 'logo' | 'done';

const BOOT_LINES = [
  '[BOOT] Initializing quantum core modules...',
  '[SYS] BIOS integrity: OK',
  '[KERNEL] Starting hyperthreaded virtual CPU...',
  '[SYS] Detecting hardware interfaces...',
  '[DEV] GPU: Neural Acceleration Unit [OK]',
  '[NET] Establishing secure uplink...',
  '[SEC] Checking encryption layers...',
  '[OK] Security protocol AES-4096 active',
  '[DRV] Mounting local drive /dev/sda1...',
  '[MEM] Allocating 512MB temporary cache...',
  '[AI] Loading R.I.A.T. tactical assistant...',
  '[AI] Neural links verified.',
  '[SYS] Initializing graphical layer...',
  '[APP] Loading interface elements...',
  '[SYS] Calibrating optical sensors...',
  '[SYS] Synchronizing system clock...',
  '[INFO] System Time: INIT / Galactic Cycle 000.0',
  '[SYS] Executing boot scripts...',
  '[OK] All systems operational.',
  '[LOGIN] Welcome, Colonel.',
  '[LOGIN] Loading secure environment...',
];

const LOGO_LINES = [
  '   _____  _____  __    __  _____  _   _ ',
  '  / ____||  __ \\|  \\  /  ||  __ \\| \\ | |',
  ' | |  __ | |  | |   \\/   || |  | |  \\| |',
  ' | | |_ || |  | | |\\  /| || |  | | . ` |',
  ' | |__| || |__| | | \\/ | || |__| | |\\  |',
  '  \\_____||_____/|_|    |_||_____/|_| \\_|',
  '                                        ',
  '    WELCOME TO R.I.A.T. SPECIAL SYSTEM',
];

export const BootPage: FC = () => {
  const navigate = useNavigate();
  const [phase, setPhase] = useState<BootPhase>('log');
  const [lines, setLines] = useState<string[]>([]);
  const [progress, setProgress] = useState(0);
  const [logoVisible, setLogoVisible] = useState(false);
  const [matrixFrame, setMatrixFrame] = useState(0);
  const cancelled = useRef(false);

  const matrixCols = useMemo(() => {
    return Array.from({ length: 80 }, () =>
      Array.from({ length: 24 }, () => (Math.random() > 0.5 ? '1' : '0')).join(''),
    );
  }, [matrixFrame]);

  const appendLine = useCallback((line: string) => {
    setLines((prev) => [...prev, line]);
  }, []);

  useEffect(() => {
    cancelled.current = false;
    let timer: number | undefined;

    async function typeBoot() {
      for (const line of BOOT_LINES) {
        if (cancelled.current) {
          return;
        }
        appendLine(line);
        await new Promise((r) => {
          timer = window.setTimeout(r, 80 + Math.random() * 120);
        });
      }
      appendLine('');
      appendLine('>>> SYSTEM ONLINE');
      appendLine('>>> Press ENTER to continue...');
      setPhase('wait1');
    }

    void typeBoot();
    return () => {
      cancelled.current = true;
      if (timer) {
        window.clearTimeout(timer);
      }
    };
  }, [appendLine]);

  useEffect(() => {
    if (phase !== 'progress') {
      return;
    }
    cancelled.current = false;
    let timer: number | undefined;
    let value = 0;

    function tick() {
      if (cancelled.current) {
        return;
      }
      value += 1;
      setProgress(value);
      if (value >= 100) {
        setLines((prev) => [
          ...prev,
          '',
          '>>> SYSTEM FULLY LOADED',
          '>>> Press ENTER to continue...',
        ]);
        setPhase('wait2');
        return;
      }
      timer = window.setTimeout(tick, 28);
    }

    setLines(['[SYSTEM] Initializing full system...', '[PROGRESS] Loading modules: 0%']);
    timer = window.setTimeout(tick, 28);
    return () => {
      cancelled.current = true;
      if (timer) {
        window.clearTimeout(timer);
      }
    };
  }, [phase]);

  useEffect(() => {
    if (phase !== 'matrix') {
      return;
    }
    let frames = 0;
    const id = window.setInterval(() => {
      frames += 1;
      setMatrixFrame(frames);
      if (frames >= 40) {
        window.clearInterval(id);
        setPhase('logo');
      }
    }, 40);
    return () => window.clearInterval(id);
  }, [phase]);

  useEffect(() => {
    if (phase !== 'logo') {
      return;
    }
    setLogoVisible(true);
    const id = window.setTimeout(() => {
      setPhase('done');
      navigate('/menu', { replace: true });
    }, 2800);
    return () => window.clearTimeout(id);
  }, [phase, navigate]);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key !== 'Enter') {
        return;
      }
      if (phase === 'wait1') {
        setPhase('progress');
      } else if (phase === 'wait2') {
        setPhase('matrix');
      }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [phase]);

  useEffect(() => {
    if (phase !== 'progress') {
      return;
    }
    setLines((prev) => {
      if (prev.length < 2) {
        return prev;
      }
      const next = [...prev];
      next[1] = `[PROGRESS] Loading modules: ${progress}%`;
      return next;
    });
  }, [progress, phase]);

  if (phase === 'matrix') {
    return (
      <div className="relative min-h-full overflow-hidden bg-riat-bg text-riat-fg font-mono text-[10px] leading-3">
        <div className="absolute inset-0 opacity-80 flex gap-1 px-1">
          {matrixCols.map((col, i) => (
            <div key={i} className="whitespace-pre opacity-70">
              {col}
            </div>
          ))}
        </div>
        <div
          className="pointer-events-none absolute left-0 right-0 h-24 bg-gradient-to-b from-transparent via-riat-fg/10 to-transparent"
          style={{ animation: 'scanline 1.2s linear infinite' }}
        />
      </div>
    );
  }

  if (phase === 'logo' || phase === 'done') {
    return (
      <div className="min-h-full flex flex-col items-center justify-center bg-riat-bg px-4">
        <pre
          className={`text-riat-fg text-[10px] sm:text-xs md:text-sm leading-tight text-center transition-opacity duration-700 ${
            logoVisible ? 'opacity-100' : 'opacity-0'
          }`}
        >
          {LOGO_LINES.join('\n')}
        </pre>
        <p className="mt-8 text-riat-dim tracking-[0.35em] uppercase text-xs">
          Initializing...
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-full bg-riat-bg p-4 md:p-8 font-mono text-sm md:text-base">
      <div className="max-w-4xl mx-auto whitespace-pre-wrap leading-relaxed">
        {lines.map((line, index) => (
          <div key={`${index}-${line}`} className="text-riat-fg">
            {line}
          </div>
        ))}
        {(phase === 'wait1' || phase === 'wait2') && (
          <button
            type="button"
            className="riat-btn mt-6"
            onClick={() => setPhase(phase === 'wait1' ? 'progress' : 'matrix')}
          >
            [ ENTER ]
          </button>
        )}
      </div>
    </div>
  );
};
