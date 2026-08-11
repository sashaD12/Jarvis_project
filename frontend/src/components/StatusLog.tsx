import type { FC } from 'react';
import { useEffect, useRef } from 'react';

interface StatusLogProps {
  lines: string[];
}

export const StatusLog: FC<StatusLogProps> = ({ lines }) => {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.scrollTop = ref.current.scrollHeight;
    }
  }, [lines]);

  return (
    <div
      ref={ref}
      className="riat-panel h-64 overflow-y-auto p-3 text-sm leading-relaxed whitespace-pre-wrap"
    >
      {lines.length === 0 ? (
        <span className="text-riat-dim">[LOG] awaiting input...</span>
      ) : (
        lines.map((line, index) => (
          <div key={`${index}-${line.slice(0, 24)}`}>{line}</div>
        ))
      )}
    </div>
  );
};
