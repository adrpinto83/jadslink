import { useQuery } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { SaaSPlan } from '@/types/plans';

/**
 * Hook para obtener los planes SaaS disponibles
 * Obtiene los datos del endpoint /api/v1/saas-plans
 * Los datos se cachean por 5 minutos
 */
export const useSaaSPlans = () => {
  return useQuery<SaaSPlan[]>({
    queryKey: ['saas-plans'],
    queryFn: async () => {
      const response = await apiClient.get('/saas-plans');
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // Cache por 5 minutos
    retry: 2,
    refetchOnWindowFocus: false,
  });
};
