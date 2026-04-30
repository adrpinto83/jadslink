import { useQuery } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { SaaSPlan } from '@/types/plans';

/**
 * Hook para obtener los planes SaaS disponibles
 * Obtiene los datos del endpoint /api/v1/saas-plans/
 * Los datos se cachean por 5 minutos
 * Se refrescan automáticamente cada 60 segundos en background
 */
export const useSaaSPlans = () => {
  return useQuery<SaaSPlan[]>({
    queryKey: ['saas-plans'],
    queryFn: async () => {
      const response = await apiClient.get('/saas-plans/');
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // Cache por 5 minutos (datos considerados frescos)
    gcTime: 30 * 60 * 1000, // Garbage collect después de 30 minutos
    retry: 2,
    refetchOnWindowFocus: false, // No refetch automático cuando vuelves a la tab
    refetchInterval: 60000, // Refetch cada 60 segundos en background (opcional, requiere enabled: true)
  });
};
