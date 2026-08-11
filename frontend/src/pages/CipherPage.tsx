import type { FC } from 'react';
import { useEffect, useState } from 'react';
import {
  adjustCipherKey,
  getCipherState,
  processCipher,
  recoverCipher,
  type CipherState,
} from '../api/client';
import { AppShell } from '../components/AppShell';

export const CipherPage: FC = () => {
  const [state, setState] = useState<CipherState | null>(null);
  const [mode, setMode] = useState<'encode' | 'decode'>('encode');
  const [input, setInput] = useState('');
  const [output, setOutput] = useState('');
  const [recoverInput, setRecoverInput] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    void getCipherState()
      .then(setState)
      .catch((err: Error) => setError(err.message));
  }, []);

  async function changeKey(delta: 1 | -1) {
    try {
      const next = await adjustCipherKey(delta);
      setState(next);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function runProcess() {
    try {
      const result = await processCipher(input, mode);
      setOutput(result.result);
      setError('');
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function runRecover() {
    const parts = recoverInput.trim().split(/\s+/).filter(Boolean);
    const numbers = parts.map((part) => Number(part));
    if (numbers.length !== 4 || numbers.some((n) => Number.isNaN(n))) {
      setError('Потрібно ввести рівно 4 числа через пробіл');
      return;
    }
    try {
      const result = await recoverCipher(numbers);
      setOutput(result.result);
      setError('');
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <AppShell title="Cipher module">
      <div className="max-w-2xl space-y-5">
        <h1 className="text-2xl tracking-widest">Шифратор / Дешифратор</h1>

        <div className="flex flex-wrap items-center gap-3">
          <span className="text-riat-dim">
            keyplus = {state?.keyplus ?? '—'} / keyminus = {state?.keyminus ?? '—'}
          </span>
          <button type="button" className="riat-btn" onClick={() => void changeKey(1)}>
            +
          </button>
          <button type="button" className="riat-btn" onClick={() => void changeKey(-1)}>
            -
          </button>
        </div>

        <div className="flex gap-4 text-sm">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="mode"
              checked={mode === 'encode'}
              onChange={() => setMode('encode')}
            />
            Зашифрувати
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="mode"
              checked={mode === 'decode'}
              onChange={() => setMode('decode')}
            />
            Розшифрувати
          </label>
        </div>

        <textarea
          className="riat-textarea min-h-24"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="текст..."
        />

        <button type="button" className="riat-btn" onClick={() => void runProcess()}>
          Виконати
        </button>

        <div>
          <div className="text-riat-dim text-xs uppercase tracking-widest mb-2">Результат</div>
          <pre className="riat-panel p-3 min-h-24 whitespace-pre-wrap text-riat-ok">{output}</pre>
        </div>

        <div className="pt-2 border-t border-riat-border space-y-3">
          <label className="block text-riat-dim text-sm">Введіть 4 числа через пробіл:</label>
          <input
            className="riat-input"
            value={recoverInput}
            onChange={(event) => setRecoverInput(event.target.value)}
            placeholder="1 2 3 4"
          />
          <button type="button" className="riat-btn" onClick={() => void runRecover()}>
            Відновити шифр
          </button>
        </div>

        {error ? <p className="text-riat-danger text-sm">{error}</p> : null}
      </div>
    </AppShell>
  );
};
