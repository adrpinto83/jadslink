import React from 'react';
import { useAuthStore } from '@/stores/auth';
import { Navigate } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { AlertCircle } from 'lucide-react';

interface AdminGuardProps {
  children: React.ReactNode;
}

export const AdminGuard: React.FC<AdminGuardProps> = ({ children }) => {
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Check if user is superadmin
  if (!user || user.role !== 'superadmin') {
    return (
      <div className="p-6">
        <Card className="border-red-200 bg-red-50 dark:bg-red-900/20">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-6 h-6 text-red-600" />
              <div>
                <h3 className="font-semibold text-red-900 dark:text-red-100">
                  Acceso Denegado
                </h3>
                <p className="text-sm text-red-800 dark:text-red-200 mt-1">
                  Esta sección solo está disponible para administradores (superadmin).
                </p>
                <p className="text-xs text-red-700 dark:text-red-300 mt-2">
                  Tu rol actual: <strong>{user?.role || 'desconocido'}</strong>
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return <>{children}</>;
};

export default AdminGuard;
