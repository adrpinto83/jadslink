import { useQuery } from '@tanstack/react-query';
import apiClient from '@/api/client';

interface LocationData {
  lat: number | null;
  lng: number | null;
  address: string;
  city: string;
  region: string;
  country: string;
  timezone: string;
}

interface GeolocationResponse {
  ip: string;
  location: LocationData;
}

/**
 * Hook to get the user's current location based on their IP address
 * Uses the backend geolocation service which queries ip-api.com
 */
export const useGeolocation = () => {
  return useQuery<GeolocationResponse>({
    queryKey: ['user-location'],
    queryFn: async () => {
      const response = await apiClient.get('/nodes/location');
      return response.data;
    },
    staleTime: 24 * 60 * 60 * 1000, // Cache for 24 hours (location doesn't change often)
    retry: 1,
  });
};

export type { LocationData, GeolocationResponse };
