import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/auth';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: 'superadmin' | 'operator';
  requiredTenantRole?: 'owner' | 'admin' | 'collaborator' | 'viewer';
}

/**
 * Componente para proteger rutas basadas en rol del usuario
 * Valida tanto el rol global (superadmin/operator) como el rol dentro del tenant
 */
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRole,
  requiredTenantRole,
}) => {
  const user = useAuthStore((state) => state.user);
  const loading = useAuthStore((state) => state.loading);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Validar rol global si se requiere
  if (requiredRole && user.role !== requiredRole) {
    return (
      <div className="flex flex-col items-center justify-center h-screen">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Acceso Denegado</h1>
        <p className="text-gray-600">No tienes permisos para acceder a esta página.</p>
        <p className="text-sm text-gray-500 mt-4">
          Rol requerido: <span className="font-semibold">{requiredRole}</span>
        </p>
      </div>
    );
  }

  // Validar rol dentro del tenant si se requiere
  if (requiredTenantRole) {
    const roleHierarchy: Record<string, number> = {
      viewer: 1,
      collaborator: 2,
      admin: 3,
      owner: 4,
    };

    const userRoleLevel = roleHierarchy[user.tenant_role || 'viewer'] || 0;
    const requiredLevel = roleHierarchy[requiredTenantRole];

    if (userRoleLevel < requiredLevel) {
      return (
        <div className="flex flex-col items-center justify-center h-screen">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Acceso Denegado</h1>
          <p className="text-gray-600">No tienes permisos suficientes para acceder a esta página.</p>
          <p className="text-sm text-gray-500 mt-4">
            Rol requerido: <span className="font-semibold">{requiredTenantRole}</span>
          </p>
        </div>
      );
    }
  }

  return <>{children}</>;
};

export default ProtectedRoute;
