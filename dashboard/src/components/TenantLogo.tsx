import React from 'react';
import { useQuery } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { Wifi } from 'lucide-react';

interface TenantData {
  id: string;
  name: string;
  plan_tier: string;
  settings?: {
    logo_url?: string;
  };
}

interface TenantLogoProps {
  /**
   * Tamaño del logo
   * 'sm' = w-8 h-8 (32px)
   * 'md' = w-12 h-12 (48px)
   * 'lg' = w-16 h-16 (64px)
   */
  size?: 'sm' | 'md' | 'lg';
  /**
   * Mostrar solo si es plan Basic/Pro (pagado)
   */
  onlyPaid?: boolean;
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

const TenantLogo: React.FC<TenantLogoProps> = ({
  size = 'sm',
  onlyPaid = false,
  className = ''
}) => {
  const { data: tenant } = useQuery<TenantData>({
    queryKey: ['tenant', 'logo'],
    queryFn: async () => {
      const response = await apiClient.get('/tenants/me');
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutos
    retry: 1,
  });

  // Si onlyPaid es true y el plan es free, mostrar icono por defecto
  if (onlyPaid && tenant?.plan_tier === 'free') {
    return (
      <div className={`${sizeMap[size]} bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center ${className}`}>
        <Wifi className="w-4 h-4 text-white" />
      </div>
    );
  }

  // Si tiene logo URL, mostrar la imagen
  if (tenant?.settings?.logo_url) {
    return (
      <img
        src={tenant.settings.logo_url}
        alt={tenant.name}
        className={`${sizeMap[size]} object-contain rounded-lg ${className}`}
      />
    );
  }

  // Por defecto, mostrar icono de WiFi con gradiente
  return (
    <div className={`${sizeMap[size]} bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center ${className}`}>
      <Wifi className="w-4 h-4 text-white" />
    </div>
  );
};

export default TenantLogo;
