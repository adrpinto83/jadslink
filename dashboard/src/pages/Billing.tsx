import React, { useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import apiClient from '@/api/client';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CreditCard, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

interface Tenant {
  id: string;
  name: string;
  slug: string;
  plan_tier: string;
  subscription_status?: string;
  stripe_customer_id?: string;
  is_active: boolean;
  created_at: string;
}

interface SubscriptionPlan {
  id: string;
  product: {
    name: string;
    description?: string;
  };
  unit_amount: number;
  currency: string;
  recurring: {
    interval: string;
    interval_count: number;
  };
}

const Billing: React.FC = () => {
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get('session_id');

  const { data: tenant, refetch: refetchTenant } = useQuery<Tenant>({
    queryKey: ['tenant', 'me'],
    queryFn: async () => {
      const response = await apiClient.get('/tenants/me');
      return response.data;
    },
  });

  const { data: plans } = useQuery<SubscriptionPlan[]>({
    queryKey: ['subscription', 'plans'],
    queryFn: async () => {
      const response = await apiClient.get('/subscriptions/plans');
      return response.data;
    },
  });

  const portalMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.get('/subscriptions/portal-session');
      return response.data;
    },
    onSuccess: (data) => {
      window.location.href = data.url;
    },
  });

  const checkoutMutation = useMutation({
    mutationFn: async (priceId: string) => {
      const response = await apiClient.post('/subscriptions/checkout-session', null, {
        params: { price_id: priceId },
      });
      return response.data;
    },
    onSuccess: (data) => {
      // Redirect to Stripe Checkout (would need Stripe.js for embedded checkout)
      // For now, assume we're redirecting via the session URL
      window.location.href = `https://checkout.stripe.com/pay/${data.sessionId}`;
    },
  });

  useEffect(() => {
    if (sessionId) {
      refetchTenant();
    }
  }, [sessionId, refetchTenant]);

  const getStatusBadge = (status?: string) => {
    const statusMap: Record<string, { variant: 'default' | 'secondary' | 'destructive'; icon: React.ReactNode }> = {
      active: { variant: 'default', icon: <CheckCircle className="w-4 h-4" /> },
      trialing: { variant: 'secondary', icon: <AlertCircle className="w-4 h-4" /> },
      past_due: { variant: 'destructive', icon: <XCircle className="w-4 h-4" /> },
      canceled: { variant: 'destructive', icon: <XCircle className="w-4 h-4" /> },
      unpaid: { variant: 'destructive', icon: <XCircle className="w-4 h-4" /> },
    };

    const config = statusMap[status || ''] || { variant: 'secondary' as const, icon: null };

    return (
      <Badge variant={config.variant} className="flex items-center gap-1 w-fit">
        {config.icon}
        {status || 'Sin suscripción'}
      </Badge>
    );
  };

  const formatPrice = (amount: number, currency: string) => {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: currency.toUpperCase(),
    }).format(amount / 100);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Facturación y Suscripción</h1>
      </div>

      {sessionId && (
        <Card className="p-6 bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
            <div>
              <h3 className="font-semibold text-green-900 dark:text-green-100">
                Suscripción Activada
              </h3>
              <p className="text-sm text-green-700 dark:text-green-300">
                Tu suscripción ha sido procesada exitosamente.
              </p>
            </div>
          </div>
        </Card>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <CreditCard className="w-5 h-5" />
            Estado de Suscripción
          </h2>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                Plan Actual
              </p>
              <p className="text-2xl font-bold capitalize">{tenant?.plan_tier || 'N/A'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Estado</p>
              {getStatusBadge(tenant?.subscription_status)}
            </div>
            {tenant?.stripe_customer_id && (
              <div className="pt-4">
                <Button
                  onClick={() => portalMutation.mutate()}
                  disabled={portalMutation.isPending}
                  className="w-full"
                >
                  {portalMutation.isPending
                    ? 'Abriendo...'
                    : 'Gestionar Suscripción en Stripe'}
                </Button>
                <p className="text-xs text-gray-500 mt-2 text-center">
                  Actualiza tu método de pago, facturas e información de facturación
                </p>
              </div>
            )}
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Límites del Plan</h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600 dark:text-gray-400">Nodos máximos</span>
              <span className="font-semibold">
                {tenant?.plan_tier === 'starter' && '5'}
                {tenant?.plan_tier === 'pro' && '20'}
                {tenant?.plan_tier === 'enterprise' && 'Ilimitado'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600 dark:text-gray-400">Tickets por mes</span>
              <span className="font-semibold">
                {tenant?.plan_tier === 'starter' && '1,000'}
                {tenant?.plan_tier === 'pro' && '10,000'}
                {tenant?.plan_tier === 'enterprise' && 'Ilimitado'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600 dark:text-gray-400">Soporte</span>
              <span className="font-semibold">
                {tenant?.plan_tier === 'starter' && 'Email'}
                {tenant?.plan_tier === 'pro' && 'Email + Chat'}
                {tenant?.plan_tier === 'enterprise' && 'Dedicado'}
              </span>
            </div>
          </div>
        </Card>
      </div>

      <div>
        <h2 className="text-2xl font-semibold mb-4">Planes Disponibles</h2>
        <div className="grid gap-6 md:grid-cols-3">
          {plans?.map((plan) => (
            <Card key={plan.id} className="p-6">
              <h3 className="text-xl font-bold mb-2">{plan.product.name}</h3>
              {plan.product.description && (
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  {plan.product.description}
                </p>
              )}
              <div className="mb-4">
                <span className="text-3xl font-bold">
                  {formatPrice(plan.unit_amount, plan.currency)}
                </span>
                <span className="text-gray-600 dark:text-gray-400">
                  /{plan.recurring.interval}
                </span>
              </div>
              <Button
                className="w-full"
                variant={
                  tenant?.plan_tier === plan.product.name.toLowerCase()
                    ? 'outline'
                    : 'default'
                }
                disabled={
                  tenant?.plan_tier === plan.product.name.toLowerCase() ||
                  checkoutMutation.isPending
                }
                onClick={() => checkoutMutation.mutate(plan.id)}
              >
                {tenant?.plan_tier === plan.product.name.toLowerCase()
                  ? 'Plan Actual'
                  : 'Seleccionar Plan'}
              </Button>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Billing;
