import type { FC } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { BootPage } from './pages/BootPage';
import { CipherPage } from './pages/CipherPage';
import { JarvisPage } from './pages/JarvisPage';
import { MapPage } from './pages/MapPage';
import { MenuPage } from './pages/MenuPage';

export const App: FC = () => {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/boot" replace />} />
      <Route path="/boot" element={<BootPage />} />
      <Route path="/menu" element={<MenuPage />} />
      <Route path="/jarvis" element={<JarvisPage />} />
      <Route path="/cipher" element={<CipherPage />} />
      <Route path="/map" element={<MapPage />} />
      <Route path="*" element={<Navigate to="/boot" replace />} />
    </Routes>
  );
};
