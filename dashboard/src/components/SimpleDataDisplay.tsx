import React, { useState, useEffect } from 'react';
import apiClient from '@/api/client';

export const SimpleDataDisplay: React.FC = () => {
  const [plans, setPlans] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        setLoading(true);
        const response = await apiClient.get('/plans');
        setPlans(response.data);
        setError(null);
      } catch (err: any) {
        setError(err.message);
        setPlans([]);
      } finally {
        setLoading(false);
      }
    };
    fetchPlans();
  }, []);

  return (
    <div className="p-6 bg-white rounded-lg shadow-lg border-2 border-green-500">
      <h2 className="text-2xl font-bold mb-4">Plans (Direct API Test)</h2>

      {loading && <p className="text-blue-600">Loading...</p>}
      {error && <p className="text-red-600">Error: {error}</p>}

      {!loading && !error && (
        <>
          <p className="text-green-600 font-bold mb-4">Total: {plans.length} plans found</p>
          {plans.length === 0 ? (
            <p className="text-gray-500">No plans found</p>
          ) : (
            <div className="space-y-3">
              {plans.map((plan: any) => (
                <div key={plan.id} className="p-3 bg-blue-50 border border-blue-200 rounded">
                  <p className="font-bold">{plan.name}</p>
                  <p className="text-sm text-gray-600">ID: {plan.id}</p>
                  <p className="text-sm text-gray-600">Duration: {plan.duration_minutes} min</p>
                  <p className="text-sm text-gray-600">Price: ${plan.price_usd}</p>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
};
