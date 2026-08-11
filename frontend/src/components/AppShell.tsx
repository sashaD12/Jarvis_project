import type { FC, PropsWithChildren } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { quitDesktopApp } from '../desktop';

interface AppShellProps extends PropsWithChildren {
  title?: string;
}

const navClass = ({ isActive }: { isActive: boolean }): string =>
  `px-3 py-1 border border-transparent hover:border-riat-border ${
    isActive ? 'text-riat-fg border-riat-border bg-riat-fg/5' : 'text-riat-dim'
  }`;

export const AppShell: FC<AppShellProps> = ({ children, title }) => {
  const navigate = useNavigate();

  return (
    <div className="min-h-full flex flex-col">
      <header className="border-b border-riat-border px-4 py-3 flex flex-wrap items-center gap-4 justify-between">
        <button
          type="button"
          className="text-left tracking-[0.25em] text-riat-fg text-lg font-bold hover:opacity-90"
          onClick={() => navigate('/menu')}
        >
          R.I.A.T.
        </button>
        <nav className="flex flex-wrap gap-2 text-sm uppercase tracking-wider">
          <NavLink to="/menu" className={navClass}>
            Menu
          </NavLink>
          <NavLink to="/jarvis" className={navClass}>
            Jarvis
          </NavLink>
          <NavLink to="/cipher" className={navClass}>
            Cipher
          </NavLink>
          <NavLink to="/map" className={navClass}>
            Map
          </NavLink>
          <button
            type="button"
            className="riat-btn riat-btn-danger px-3 py-1 text-sm uppercase tracking-wider"
            onClick={() => quitDesktopApp()}
          >
            Exit
          </button>
        </nav>
      </header>
      {title ? (
        <div className="px-4 pt-4 text-riat-dim text-xs uppercase tracking-[0.3em]">{title}</div>
      ) : null}
      <main className="flex-1 p-4">{children}</main>
    </div>
  );
};
