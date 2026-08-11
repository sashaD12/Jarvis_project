import type { FC } from 'react';

interface ConfirmModalProps {
  open: boolean;
  title: string;
  message: string;
  onAccept: () => void;
  onDecline: () => void;
}

export const ConfirmModal: FC<ConfirmModalProps> = ({
  open,
  title,
  message,
  onAccept,
  onDecline,
}) => {
  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4">
      <div className="riat-panel max-w-md w-full p-5">
        <h2 className="text-riat-fg text-lg tracking-widest mb-3">{title}</h2>
        <p className="text-riat-dim mb-6 whitespace-pre-wrap">{message}</p>
        <div className="flex gap-3 justify-end">
          <button type="button" className="riat-btn" onClick={onDecline}>
            Ні
          </button>
          <button type="button" className="riat-btn riat-btn-danger" onClick={onAccept}>
            Так
          </button>
        </div>
      </div>
    </div>
  );
};
