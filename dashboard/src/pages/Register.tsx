import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface RegisterForm {
  company_name: string;
  email: string;
  password: string;
  confirmPassword: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const Register: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState<RegisterForm>({
    company_name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const registerMutation = useMutation({
    mutationFn: async (data: Omit<RegisterForm, 'confirmPassword'>) => {
      return await axios.post(`${API_BASE_URL}/auth/register`, data);
    },
    onSuccess: () => {
      setSuccess(true);
      setError('');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Error al registrarse';
      setError(message);
      setSuccess(false);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Las contraseñas no coinciden');
      return;
    }

    if (formData.password.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres');
      return;
    }

    const { confirmPassword, ...registerData } = formData;
    registerMutation.mutate(registerData);
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-gray-900 dark:to-gray-800 px-4">
        <Card className="w-full max-w-md p-8 shadow-xl">
          <div className="text-center">
            <div className="mb-4 text-6xl">✓</div>
            <h1 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">¡Bienvenido a JADSlink!</h1>
            <div className="mb-6 space-y-3 text-left">
              <p className="text-gray-600 dark:text-gray-400">
                Tu cuenta ha sido creada exitosamente con <span className="font-semibold text-blue-600 dark:text-blue-400">Plan Free</span>.
              </p>
              <p className="text-gray-600 dark:text-gray-400 font-semibold mb-2">
                Incluye:
              </p>
              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1 ml-4">
                <li>✓ 1 nodo para comenzar</li>
                <li>✓ 50 tickets gratis para demostración</li>
                <li>✓ Acceso inmediato al dashboard</li>
              </ul>
            </div>
            <Button onClick={() => navigate('/login')} className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700">
              Iniciar Sesión Ahora
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-gray-900 dark:to-gray-800 px-4 py-8">
      <Card className="w-full max-w-lg p-8 shadow-xl">
        <div className="text-center mb-8">
          <div className="w-14 h-14 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center mx-auto mb-4 shadow-lg">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.111 16.251a.75.75 0 00.75-.75v-6a.75.75 0 00-1.5 0v6c0 .414.336.75.75.75z" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold mb-2 text-gray-900 dark:text-white">JADSlink</h1>
          <p className="text-gray-600 dark:text-gray-400">Crea tu cuenta en segundos</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <Label htmlFor="company_name" className="text-sm font-medium">Nombre de la Empresa *</Label>
            <Input
              id="company_name"
              type="text"
              value={formData.company_name}
              onChange={(e) =>
                setFormData({ ...formData, company_name: e.target.value })
              }
              placeholder="Mi Empresa S.A."
              required
              autoComplete="organization"
              className="h-10"
            />
          </div>

          <div>
            <Label htmlFor="email" className="text-sm font-medium">Email *</Label>
            <Input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              placeholder="email@empresa.com"
              required
              autoComplete="email"
              className="h-10"
            />
          </div>

          <div>
            <Label htmlFor="password" className="text-sm font-medium">Contraseña *</Label>
            <Input
              id="password"
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              placeholder="••••••••"
              required
              minLength={8}
              autoComplete="new-password"
              className="h-10"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Mínimo 8 caracteres</p>
          </div>

          <div>
            <Label htmlFor="confirmPassword" className="text-sm font-medium">Confirmar Contraseña *</Label>
            <Input
              id="confirmPassword"
              type="password"
              value={formData.confirmPassword}
              onChange={(e) =>
                setFormData({ ...formData, confirmPassword: e.target.value })
              }
              placeholder="••••••••"
              required
              minLength={8}
              autoComplete="new-password"
              className="h-10"
            />
          </div>

          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 px-4 py-3 rounded-lg flex items-start gap-2">
              <span className="text-lg">⚠️</span>
              <span className="text-sm">{error}</span>
            </div>
          )}

          <Button
            type="submit"
            className="w-full h-10 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold shadow-md hover:shadow-lg transition-all"
            disabled={registerMutation.isPending}
          >
            {registerMutation.isPending ? 'Creando cuenta...' : 'Crear Cuenta'}
          </Button>
        </form>

        <div className="mt-6 text-center border-t border-gray-200 dark:border-gray-700 pt-6">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            ¿Ya tienes una cuenta?{' '}
            <Link
              to="/login"
              className="text-blue-600 dark:text-blue-400 hover:underline font-medium"
            >
              Inicia sesión aquí
            </Link>
          </p>
        </div>
      </Card>
    </div>
  );
};

export default Register;
