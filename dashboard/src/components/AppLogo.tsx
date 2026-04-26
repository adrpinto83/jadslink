import React, { useEffect, useState } from 'react';
import { Wifi } from 'lucide-react';
import apiClient from '@/api/client';

interface AppLogoProps {
  /**
   * Tamaño del logo
   * 'sm' = w-8 h-8 (32px)
   * 'md' = w-12 h-12 (48px)
   * 'lg' = w-16 h-16 (64px)
   */
  size?: 'sm' | 'md' | 'lg';
  /**
   * Classes adicionales
   */
  className?: string;
}

const sizeMap = {
  sm: 'w-8 h-8',
  md: 'w-12 h-12',
  lg: 'w-16 h-16',
};

const AppLogo: React.FC<AppLogoProps> = ({
  size = 'sm',
  className = ''
}) => {
  const [logoUrl, setLogoUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Obtener logo de JADSlink (público, sin autenticación)
    apiClient
      .get('/admin/logo/public')
      .then((response) => {
        if (response.data.logo_url) {
          setLogoUrl(response.data.logo_url);
        }
      })
      .catch((error) => {
        console.error("Error cargando logo de JADSlink:", error);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  // Si tiene logo personalizado, mostrar la imagen
  if (logoUrl && !loading) {
    return (
      <img
        src={logoUrl}
        alt="JADSlink"
        className={`${sizeMap[size]} object-contain rounded-lg ${className}`}
      />
    );
  }

  // Por defecto, mostrar icono de WiFi con gradiente azul
  return (
    <div className={`${sizeMap[size]} bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center ${className}`}>
      <Wifi className="w-4 h-4 text-white" />
    </div>
  );
};

export default AppLogo;
