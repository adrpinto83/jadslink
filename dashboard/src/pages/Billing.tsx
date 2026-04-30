import React, { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import apiClient from '@/api/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, XCircle, AlertCircle, Gift } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { UpgradeOptions } from '@/components/UpgradeOptions';
import { PaymentMethodSelector } from '@/components/PaymentMethodSelector';
import { PagoMovilForm } from '@/components/PagoMovilForm';
import { UpgradeRequestsHistory } from '@/components/UpgradeRequestsHistory';
import { useSaaSPlans } from '@/hooks/useSaaSPlans';

interface Tenant {
  id: string;
  name: string;
  slug: string;
  plan_tier: string;
  subscription_status?: string;
  stripe_customer_id?: string;
  is_active: boolean;
  created_at: string;
  extra_tickets_count?: number;
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

interface UsageData {
  plan_tier: string;
  subscription_status: string;
  nodes: {
    used: number;
    limit: number;
    unlimited: boolean;
  };
  tickets: {
    used: number;
    limit: number;
    unlimited: boolean;
  };
}

interface UpgradeRequest {
  id: string;
  upgrade_type: 'extra_tickets' | 'plan_upgrade';
  amount_usd: number;
  amount_vef: number;
  status: 'pending_payment' | 'payment_received' | 'approved' | 'rejected' | 'cancelled';
  ticket_quantity?: number;
  new_plan_tier?: string;
  payment_method: 'pago_movil' | 'card';
  banco_origen?: string;
  referencia_pago?: string;
  created_at: string;
  reminder_count: number;
}

interface PricingConfig {
  id: string;
  ticket_pack_size: number;
  ticket_pack_price_usd: string | number;
  additional_node_price_usd: string | number;
  free_plan_max_nodes: number;
  free_plan_max_tickets: number;
  basic_plan_max_nodes: number;
  basic_plan_max_free_tickets: number;
  description: string;
  created_at: string;
  updated_at: string;
}

const Billing: React.FC = () => {
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get('session_id');
  const queryClient = useQueryClient();

  // State para el flujo de upgrade
  const [selectedPlan, setSelectedPlan] = useState<'extra_tickets' | 'plan_basic' | 'plan_pro' | null>(null);
  const [paymentMethod, setPaymentMethod] = useState<'pago_movil' | 'card' | null>(null);
  const [exchangeRate, setExchangeRate] = useState<number>(36.5);

  // Query para obtener tasa de cambio dinámica
  const { data: exchangeRateData } = useQuery({
    queryKey: ['exchange-rate'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/utils/exchange-rate');
        return response.data;
      } catch (error: any) {
        // Si el endpoint no existe, usar tasa por defecto
        console.warn('exchange-rate endpoint not available, using default rate');
        return { rate: 36.5 };
      }
    },
    refetchInterval: 60000, // Refrescar cada minuto
  });

  // Actualizar tasa cuando se obtenga del servidor
  useEffect(() => {
    if (exchangeRateData?.rate) {
      setExchangeRate(Number(exchangeRateData.rate));
    }
  }, [exchangeRateData]);

  // Query para obtener configuración de precios dinámica
  const { data: pricingConfig } = useQuery<PricingConfig>({
    queryKey: ['pricing-config'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/admin/pricing');
        return response.data;
      } catch (error: any) {
        // Si el endpoint no existe, usar valores por defecto
        console.warn('pricing endpoint not available, using default config');
        return {
          id: 'default',
          ticket_pack_size: 50,
          ticket_pack_price_usd: 0.5,
          additional_node_price_usd: 10,
          free_plan_max_nodes: 1,
          free_plan_max_tickets: 50,
          basic_plan_max_nodes: 3,
          basic_plan_max_free_tickets: 1000,
          description: 'Configuración por defecto',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
      }
    },
    refetchInterval: 60000, // Refrescar cada minuto
  });

  const { data: tenant, refetch: refetchTenant } = useQuery<Tenant>({
    queryKey: ['tenant', 'me'],
    queryFn: async () => {
      const response = await apiClient.get('/tenants/me');
      return response.data;
    },
  });

  const { data: usage, refetch: refetchUsage } = useQuery<UsageData>({
    queryKey: ['tenant', 'usage'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/tenants/me/usage');
        return response.data;
      } catch (error: any) {
        // Si el endpoint no existe, retornar datos por defecto
        console.warn('usage endpoint not available, using default data');
        return {
          plan_tier: 'free',
          subscription_status: 'active',
          nodes: { used: 0, limit: 1, unlimited: false },
          tickets: { used: 0, limit: 50, unlimited: false },
        };
      }
    },
  });

  // Obtener planes SaaS mejorados
  const { data: saasPlans = [] } = useSaaSPlans();

  const { data: upgradeRequests = [], refetch: refetchRequests, isLoading: isLoadingRequests } = useQuery<UpgradeRequest[]>({
    queryKey: ['subscriptions', 'my-requests'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/subscriptions/my-requests');
        return response.data;
      } catch (error: any) {
        // Si el endpoint no existe (404, 500), retornar lista vacía
        console.warn('my-requests endpoint not available, using empty list');
        return [];
      }
    },
    refetchInterval: 10000, // Refetch cada 10 segundos
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
      window.location.href = `https://checkout.stripe.com/pay/${data.sessionId}`;
    },
  });

  const upgradeRequestMutation = useMutation({
    mutationFn: async (data: {
      upgrade_type: 'extra_tickets' | 'plan_upgrade';
      ticket_quantity?: number;
      new_plan_tier?: string;
      payment_method: 'pago_movil' | 'card';
      payment_details?: {
        banco_origen: string;
        cédula_pagador: string;
        referencia_pago: string;
        comprobante_url: string;
      };
    }) => {
      const response = await apiClient.post('/subscriptions/request-upgrade', data);
      return response.data;
    },
    onSuccess: () => {
      refetchRequests();
      // Limpiar el formulario
      setSelectedPlan(null);
      setPaymentMethod(null);
      queryClient.invalidateQueries({ queryKey: ['subscriptions', 'my-requests'] });
    },
  });

  useEffect(() => {
    if (sessionId) {
      refetchTenant();
      refetchUsage();
    }
  }, [sessionId, refetchTenant, refetchUsage]);

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

  const convertToVEF = (usdAmount: number): number => {
    return Math.round(usdAmount * exchangeRate * 100) / 100;
  };

  const renderPlanPrice = (plan: SubscriptionPlan) => {
    const priceUSD = plan.unit_amount / 100;
    const priceVEF = convertToVEF(priceUSD);

    return (
      <div className="space-y-1">
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold">${priceUSD.toFixed(2)}</span>
          <span className="text-gray-600 dark:text-gray-400">USD</span>
        </div>
        <div className="text-sm text-gray-500 dark:text-gray-400">
          ≈ Bs. {priceVEF.toLocaleString('es-ES')}
        </div>
      </div>
    );
  };

  const getProgressColor = (percentage: number) => {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const renderUsageBar = (used: number, limit: number, unlimited: boolean, label: string) => {
    if (unlimited) {
      return (
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">{label}</span>
            <span className="text-sm font-semibold">Sin límite</span>
          </div>
        </div>
      );
    }

    const percentage = Math.min((used / limit) * 100, 100);
    const isWarning = percentage >= 70;

    return (
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600 dark:text-gray-400">{label}</span>
          <span className={`text-sm font-semibold ${isWarning ? 'text-orange-600 dark:text-orange-400' : ''}`}>
            {used} / {limit}
          </span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${getProgressColor(percentage)}`}
            style={{ width: `${percentage}%` }}
          />
        </div>
        {isWarning && (
          <p className="text-xs text-orange-600 dark:text-orange-400 flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />
            Acercándote al límite
          </p>
        )}
      </div>
    );
  };

  const handlePagoMovilSubmit = async (data: {
    banco_origen: string;
    cédula_pagador: string;
    referencia_pago: string;
    comprobante_url: string;
  }) => {
    if (!selectedPlan) return;

    let upgradeData: any = {
      upgrade_type: selectedPlan === 'extra_tickets' ? 'extra_tickets' : 'plan_upgrade',
      payment_method: 'mobile_pay',
      payment_details: data,
    };

    if (selectedPlan === 'extra_tickets') {
      upgradeData.ticket_quantity = 50;
    } else if (selectedPlan === 'plan_basic') {
      upgradeData.new_plan_tier = 'basic';
    } else if (selectedPlan === 'plan_pro') {
      upgradeData.new_plan_tier = 'pro';
    }

    upgradeRequestMutation.mutate(upgradeData);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Facturación y Planes</h1>
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

      {/* Grid de información del tenant */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="p-4">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-600 dark:text-gray-400">Plan Actual</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold capitalize">{tenant?.plan_tier || 'free'}</p>
            {getStatusBadge(tenant?.subscription_status)}
          </CardContent>
        </Card>

        <Card className="p-4">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-600 dark:text-gray-400">Tickets Disponibles</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold flex items-center gap-2">
              <Gift className="w-6 h-6" />
              {tenant?.extra_tickets_count || 0}
            </p>
            <p className="text-xs text-gray-500 mt-1">+ 50 tickets gratis del plan</p>
          </CardContent>
        </Card>

        <Card className="p-4">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-600 dark:text-gray-400">Solicitudes Pendientes</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              {upgradeRequests.filter(r => r.status === 'pending_payment').length}
            </p>
            <p className="text-xs text-gray-500 mt-1">En proceso de confirmación</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs principales */}
      <Tabs defaultValue="comprar" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="comprar">Comprar o Actualizar</TabsTrigger>
          <TabsTrigger value="historial">Historial de Solicitudes</TabsTrigger>
        </TabsList>

        {/* Tab: Comprar/Actualizar */}
        <TabsContent value="comprar" className="space-y-6">
          {/* Step 1: Seleccionar Plan */}
          <div>
            <h2 className="text-2xl font-semibold mb-4">Paso 1: Elige qué deseas</h2>
            <UpgradeOptions
              currentPlan={(tenant?.plan_tier as any) || 'free'}
              ticketsAvailable={tenant?.extra_tickets_count || 0}
              onSelect={setSelectedPlan}
              isLoading={upgradeRequestMutation.isPending}
              pricingConfig={pricingConfig}
            />
          </div>

          {selectedPlan && (
            <>
              {/* Step 2: Método de Pago */}
              <div>
                <h2 className="text-2xl font-semibold mb-4">Paso 2: Elige método de pago</h2>
                <PaymentMethodSelector
                  selected={paymentMethod}
                  onSelect={setPaymentMethod}
                />
              </div>

              {/* Step 3: Completar Detalles de Pago */}
              {paymentMethod === 'pago_movil' && (
                <div>
                  <h2 className="text-2xl font-semibold mb-4">Paso 3: Detalles de Pago Móvil</h2>
                  <PagoMovilForm
                    onSubmit={handlePagoMovilSubmit}
                    isLoading={upgradeRequestMutation.isPending}
                    exchangeRate={exchangeRate}
                    amountUsd={
                      selectedPlan === 'extra_tickets'
                        ? Number(pricingConfig?.ticket_pack_price_usd || 0.5)
                        : selectedPlan === 'plan_basic'
                        ? Number(pricingConfig?.additional_node_price_usd || 29)
                        : Number(pricingConfig?.additional_node_price_usd || 99) * 2
                    }
                  />
                </div>
              )}

              {paymentMethod === 'card' && (
                <Card className="p-6 bg-yellow-50 dark:bg-yellow-950 border-yellow-200 dark:border-yellow-800">
                  <div className="flex items-center gap-3">
                    <AlertCircle className="w-6 h-6 text-yellow-600" />
                    <div>
                      <h3 className="font-semibold text-yellow-900 dark:text-yellow-100">
                        Integración en Desarrollo
                      </h3>
                      <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                        Los pagos con tarjeta estará disponible muy pronto. Por ahora, usa Pago Móvil.
                      </p>
                    </div>
                  </div>
                </Card>
              )}
            </>
          )}

          {!selectedPlan && (
            <Card className="p-6 bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800">
              <AlertCircle className="w-6 h-6 text-blue-600 mb-2" />
              <p className="text-blue-900 dark:text-blue-100">
                Selecciona una opción de compra arriba para comenzar.
              </p>
            </Card>
          )}
        </TabsContent>

        {/* Tab: Historial */}
        <TabsContent value="historial">
          <UpgradeRequestsHistory
            requests={upgradeRequests}
            isLoading={isLoadingRequests}
          />
        </TabsContent>
      </Tabs>

      {/* Planes SaaS - Mejorados */}
      {saasPlans && saasPlans.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-semibold">Planes SaaS Disponibles</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Elige el plan que mejor se ajuste a tus necesidades
              </p>
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {saasPlans.map((plan) => {
              const isCurrentPlan = tenant?.plan_tier === plan.tier;

              return (
                <Card key={plan.tier} className={`p-6 relative transition-all flex flex-col ${
                  isCurrentPlan ? 'ring-2 ring-blue-500' : ''
                } ${plan.is_recommended ? 'border-purple-500 border-2' : ''}`}>
                  {isCurrentPlan && (
                    <Badge className="absolute top-4 right-4 bg-blue-500">
                      ✓ Plan Actual
                    </Badge>
                  )}

                  {plan.badge && (
                    <Badge className="absolute -top-3 left-1/2 -translate-x-1/2 bg-purple-600">
                      {plan.badge}
                    </Badge>
                  )}

                  <div className="mb-4 flex-grow">
                    <h3 className="text-xl font-bold mb-2">{plan.name}</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                      {plan.description}
                    </p>

                    <div className="mb-4 pb-4 border-b border-gray-200 dark:border-gray-700">
                      <p className="text-3xl font-bold">${plan.monthly_price.toFixed(0)}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">/mes</p>
                    </div>

                    {/* Features */}
                    <ul className="space-y-2 text-sm">
                      {plan.features.slice(0, 4).map((feature, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <CheckCircle className={`w-4 h-4 mt-0.5 flex-shrink-0 ${
                            feature.included ? 'text-green-600' : 'text-gray-400'
                          }`} />
                          <span className={feature.included ? '' : 'text-gray-400'}>
                            {feature.text}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <Button
                    className="w-full mt-4"
                    variant={isCurrentPlan ? 'outline' : 'default'}
                    disabled={isCurrentPlan}
                  >
                    {isCurrentPlan ? 'Plan Activo' : 'Seleccionar'}
                  </Button>
                </Card>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default Billing;
