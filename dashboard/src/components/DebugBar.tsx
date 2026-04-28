import React, { useState, useEffect } from 'react';
import { useAuthStore } from '@/stores/auth';
import apiClient from '@/api/client';

export const DebugBar: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [debug, setDebug] = useState<any>({});
  const [endpoints, setEndpoints] = useState<any>({});
  const accessToken = useAuthStore((state) => state.accessToken);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  useEffect(() => {
    const updateDebug = async () => {
      try {
        const response = await apiClient.get('/auth/me');

        // Test all endpoints
        const endpointTests: any = {};
        const endpoints_to_test = ['/plans', '/nodes', '/tickets', '/sessions'];

        for (const endpoint of endpoints_to_test) {
          try {
            const result = await apiClient.get(endpoint);
            endpointTests[endpoint] = {
              status: 'OK',
              count: Array.isArray(result.data) ? result.data.length : 'object'
            };
          } catch (err: any) {
            endpointTests[endpoint] = {
              status: 'ERROR',
              code: err.response?.status || err.message
            };
          }
        }

        setEndpoints(endpointTests);
        setDebug({
          apiUrl: apiClient.defaults.baseURL,
          token: accessToken ? `${accessToken.substring(0, 20)}...` : 'null',
          isAuthenticated,
          user: response.data,
          status: 'OK'
        });
      } catch (error: any) {
        setDebug({
          apiUrl: apiClient.defaults.baseURL,
          token: accessToken ? `${accessToken.substring(0, 20)}...` : 'null',
          isAuthenticated,
          error: error.response?.status || error.message,
          status: 'ERROR'
        });
      }
    };
    updateDebug();
  }, [accessToken, isAuthenticated]);

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-4 right-4 px-3 py-2 bg-blue-600 text-white text-xs rounded z-50 hover:bg-blue-700"
      >
        Debug
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 bg-black text-white text-xs p-4 rounded max-w-md z-50 max-h-96 overflow-auto font-mono border border-green-500">
      <button
        onClick={() => setIsOpen(false)}
        className="float-right text-red-400 hover:text-red-600 font-bold"
      >
        ✕
      </button>
      <div className="clear-both mb-2 font-bold">DEBUG INFO</div>
      <pre>{JSON.stringify(debug, null, 2)}</pre>
      <div className="mt-4 font-bold border-t border-green-500 pt-2">ENDPOINTS</div>
      <pre>{JSON.stringify(endpoints, null, 2)}</pre>
    </div>
  );
};
