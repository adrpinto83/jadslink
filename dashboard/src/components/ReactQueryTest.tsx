import React from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/api/client';

export const ReactQueryTest: React.FC = () => {
  const queryClient = useQueryClient();

  const { data: plans, isLoading, error } = useQuery({
    queryKey: ['test-plans'],
    queryFn: async () => {
      const response = await apiClient.get('/plans');
      return response.data;
    }
  });

  const handleClearCache = () => {
    queryClient.clear();
    queryClient.refetchQueries();
  };

  return (
    <div className="p-6 bg-yellow-50 rounded-lg border-2 border-yellow-500 mt-6">
      <h2 className="text-2xl font-bold mb-4">React Query Test</h2>

      <button
        onClick={handleClearCache}
        className="mb-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
      >
        Clear React Query Cache
      </button>

      {isLoading && <p className="text-blue-600">Loading with React Query...</p>}
      {error && <p className="text-red-600">Error with React Query: {String(error)}</p>}

      {!isLoading && !error && (
        <>
          <p className="text-green-600 font-bold mb-4">React Query loaded: {plans?.length || 0} plans</p>
          {plans && plans.length > 0 ? (
            <div className="space-y-2">
              {plans.map((plan: any) => (
                <div key={plan.id} className="p-2 bg-white border border-yellow-200 rounded">
                  <p className="font-bold">{plan.name}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500">No plans loaded</p>
          )}
        </>
      )}
    </div>
  );
};
