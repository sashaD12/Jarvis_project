import type { FC } from 'react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getNews } from '../api/client';
import { AppShell } from '../components/AppShell';

export const MenuPage: FC = () => {
  const [news, setNews] = useState('Завантаження новин...');
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    void getNews()
      .then((data) => {
        if (active) {
          setNews(data.text);
        }
      })
      .catch((err: Error) => {
        if (active) {
          setError(err.message);
          setNews('');
        }
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <AppShell title="Main uplink">
      <div className="grid gap-8 lg:grid-cols-[1fr_1.2fr] max-w-6xl">
        <section>
          <h1 className="text-3xl tracking-[0.2em] mb-2">R.I.A.T.</h1>
          <p className="text-riat-dim mb-8 max-w-md">
            Tactical assistant uplink. Select a module to proceed.
          </p>
          <div className="flex flex-col gap-3 max-w-xs">
            <Link to="/jarvis" className="riat-btn text-left">
              &gt; Jarvis Assistant
            </Link>
            <Link to="/cipher" className="riat-btn text-left">
              &gt; Cipher Tool
            </Link>
            <Link to="/map" className="riat-btn text-left">
              &gt; System Map
            </Link>
          </div>
        </section>
        <section className="riat-panel p-4">
          <h2 className="tracking-[0.25em] uppercase text-sm mb-4 text-riat-dim">
            Головні новини
          </h2>
          {error ? (
            <p className="text-riat-danger">{error}</p>
          ) : (
            <pre className="whitespace-pre-wrap text-sm text-riat-fg/90 leading-relaxed font-mono">
              {news}
            </pre>
          )}
        </section>
      </div>
    </AppShell>
  );
};
