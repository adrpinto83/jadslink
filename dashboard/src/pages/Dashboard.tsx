import React from 'react';
import { useAuthStore } from '@/stores/auth';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';

const Dashboard: React.FC = () => {
  const logout = useAuthStore((state) => state.logout);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100 dark:bg-gray-950">
      <div className="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md dark:bg-gray-800">
        <h2 className="text-2xl font-bold text-center text-gray-900 dark:text-gray-100">Dashboard</h2>
        <p className="text-center text-gray-700 dark:text-gray-300">¡Bienvenido a tu panel de control!</p>
        <Button onClick={handleLogout} className="w-full">
          Cerrar Sesión
        </Button>
      </div>
    </div>
  );
};

export default Dashboard;
