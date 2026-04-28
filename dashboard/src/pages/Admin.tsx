import React from 'react';
import { Link } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { DollarSign, BarChart3, Settings, CreditCard, Users, Gift } from 'lucide-react';

const Admin: React.FC = () => {
  const adminSections = [
    {
      title: 'Gestión de Pagos',
      description: 'Revisa solicitudes de pago de clientes, aprueba o rechaza',
      icon: CreditCard,
      href: 'payments',
      color: 'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400',
    },
    {
      title: 'Configuración de Precios',
      description: 'Modifica costos de tickets, nodos y límites de planes',
      icon: DollarSign,
      href: 'pricing',
      color: 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400',
    },
    {
      title: 'Análisis Global',
      description: 'Estadísticas de la plataforma, tenants activos, nodos online',
      icon: BarChart3,
      href: '#',
      color: 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400',
      disabled: true,
    },
    {
      title: 'Gestión de Tenants',
      description: 'Aprobar nuevos operadores, suspender cuentas',
      icon: Settings,
      href: '#',
      color: 'bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400',
      disabled: true,
    },
    {
      title: 'Gestión de Empleados',
      description: 'Administra empleados y roles de cualquier operador',
      icon: Users,
      href: 'users',
      color: 'bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400',
    },
    {
      title: 'Suscripciones Gratuitas',
      description: 'Otorga planes PRO gratis a operadores (pruebas, promociones)',
      icon: Gift,
      href: 'subscriptions',
      color: 'bg-pink-50 dark:bg-pink-900/20 text-pink-600 dark:text-pink-400',
    },
  ];

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-3xl font-bold">Panel de Administración</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Gestiona la configuración global de JADSlink
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {adminSections.map((section) => {
          const Icon = section.icon;
          return (
            <Card key={section.title} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className={`w-12 h-12 rounded-lg ${section.color} flex items-center justify-center mb-4`}>
                  <Icon className="w-6 h-6" />
                </div>
                <CardTitle>{section.title}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {section.description}
                </p>
                {!section.disabled ? (
                  <Link to={section.href} className="block">
                    <Button className="w-full bg-blue-600 hover:bg-blue-700">
                      Acceder
                    </Button>
                  </Link>
                ) : (
                  <Button className="w-full" disabled>
                    Próximamente
                  </Button>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
};

export default Admin;
