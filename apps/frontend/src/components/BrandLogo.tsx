import { useMemo, useState } from 'react';

type BrandLogoProps = {
  className?: string;
};

export default function BrandLogo({ className }: BrandLogoProps) {
  const [failed, setFailed] = useState(false);
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  const src = useMemo(() => {
    const trimmed = String(baseUrl).replace(/\/+$/, '');
    return `${trimmed}/api/v1/assets/logo`;
  }, [baseUrl]);

  if (failed) {
    // Fallback (in case backend not running yet)
    return (
      <div
        className={
          className ??
          'w-10 h-10 bg-accent-blue rounded-lg flex items-center justify-center'
        }
        aria-label="AXDATA"
        role="img"
      >
        <span className="text-white font-bold text-xl">AX</span>
      </div>
    );
  }

  return (
    <img
      src={src}
      alt="AXDATA"
      className={className ?? 'h-10 w-auto'}
      onError={() => setFailed(true)}
      loading="eager"
      decoding="async"
    />
  );
}

