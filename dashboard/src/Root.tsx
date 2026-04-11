import React from 'react';
import { useAuthStore } from './stores/auth';
import { Navigate } from 'react-router-dom';

const Root: React.FC = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Navigate to="/login" replace />;
};

export default Root;
