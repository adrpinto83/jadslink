import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Gift, AlertCircle, Check, X } from 'lucide-react';
import { toast } from 'sonner';

interface Tenant {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
}

interface SubscriptionInfo {
  plan_tier: string;
  subscription_status: string;
  free_subscription_until: string | null;
  free_subscription_plan: string | null;
  free_subscription_reason: string | null;
  is_free_subscription_active: boolean;
}

const AdminSubscriptions: React.FC = () => {
  const [selectedTenantId, setSelectedTenantId] = useState<string | null>(null);
  const [grantDialogOpen, setGrantDialogOpen] = useState(false);
  const [grantFormData, setGrantFormData] = useState({
    plan: 'pro',
    days: 30,
    reason: '',
  });
  const queryClient = useQueryClient();

  // Obtener lista de tenants
  const { data: tenants, isLoading: tenantsLoading } = useQuery<Tenant[]>({
    queryKey: ['admin', 'tenants'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/tenants');
      return response.data;
    },
  });

  // Obtener información de suscripción del tenant seleccionado
  const { data: subscriptionInfo, isLoading: subscriptionLoading } = useQuery<SubscriptionInfo>({
    queryKey: ['admin', 'subscription', selectedTenantId],
    queryFn: async () => {
      if (!selectedTenantId) return null;
      const response = await apiClient.get(`/admin/tenants/${selectedTenantId}/subscription`);
      return response.data;
    },
    enabled: !!selectedTenantId,
  });

  // Otorgar suscripción gratuita
  const grantMutation = useMutation({
    mutationFn: async (data: typeof grantFormData) => {
      if (!selectedTenantId) throw new Error('Tenant no seleccionado');
      await apiClient.post(`/admin/tenants/${selectedTenantId}/subscription/grant`, {
        plan: data.plan,
        days: data.days,
        reason: data.reason || undefined,
      });
    },
    onSuccess: () => {
      toast.success('Suscripción gratuita otorgada');
      setGrantDialogOpen(false);
      setGrantFormData({ plan: 'pro', days: 30, reason: '' });
      if (selectedTenantId) {
        queryClient.invalidateQueries({ queryKey: ['admin', 'subscription', selectedTenantId] });
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Error al otorgar suscripción');
    },
  });

  // Revocar suscripción gratuita
  const revokeMutation = useMutation({
    mutationFn: async () => {
      if (!selectedTenantId) throw new Error('Tenant no seleccionado');
      await apiClient.post(`/admin/tenants/${selectedTenantId}/subscription/revoke`);
    },
    onSuccess: () => {
      toast.success('Suscripción gratuita revocada');
      if (selectedTenantId) {
        queryClient.invalidateQueries({ queryKey: ['admin', 'subscription', selectedTenantId] });
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Error al revocar suscripción');
    },
  });

  const selectedTenant = tenants?.find((t) => t.id === selectedTenantId);
  const getPlanColor = (plan: string) => {
    switch (plan) {
      case 'pro':
        return 'bg-purple-100 text-purple-800';
      case 'basic':
        return 'bg-blue-100 text-blue-800';
      case 'free':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status: string, isFreeActive: boolean) => {
    if (isFreeActive) {
      return 'bg-green-100 text-green-800';
    }
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'trialing':
        return 'bg-blue-100 text-blue-800';
      case 'past_due':
        return 'bg-yellow-100 text-yellow-800';
      case 'canceled':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Gestión de Suscripciones</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Otorga y revoca suscripciones gratuitas PRO a operadores
        </p>
      </div>

      {/* Selector de Tenant */}
      <Card>
        <CardHeader>
          <CardTitle>Seleccionar Operador</CardTitle>
          <CardDescription>Elige un operador para gestionar su suscripción</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Label htmlFor="tenant-select">Operador/Tenant</Label>
            <Select value={selectedTenantId || ''} onValueChange={setSelectedTenantId}>
              <SelectTrigger id="tenant-select">
                <SelectValue placeholder="Selecciona un operador..." />
              </SelectTrigger>
              <SelectContent>
                {tenantsLoading ? (
                  <div className="p-2 text-sm text-gray-500">Cargando...</div>
                ) : !tenants || tenants.length === 0 ? (
                  <div className="p-2 text-sm text-gray-500">No hay operadores</div>
                ) : (
                  tenants.map((tenant) => (
                    <SelectItem key={tenant.id} value={tenant.id}>
                      <div className="flex items-center gap-2">
                        <span>{tenant.name}</span>
                        {!tenant.is_active && (
                          <Badge variant="outline" className="text-xs">
                            Inactivo
                          </Badge>
                        )}
                      </div>
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Información de Suscripción */}
      {selectedTenantId && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Gift className="w-5 h-5" />
              Información de Suscripción
            </CardTitle>
            <CardDescription>{selectedTenant?.name}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {subscriptionLoading ? (
              <div className="flex items-center justify-center py-8">
                <p className="text-gray-500">Cargando información...</p>
              </div>
            ) : subscriptionInfo ? (
              <>
                {/* Plan Actual */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-sm font-semibold">Plan Actual</Label>
                    <div className="flex items-center gap-2">
                      <Badge className={getPlanColor(subscriptionInfo.plan_tier)}>
                        {subscriptionInfo.plan_tier.toUpperCase()}
                      </Badge>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-sm font-semibold">Estado de Suscripción</Label>
                    <Badge
                      className={getStatusColor(
                        subscriptionInfo.subscription_status,
                        subscriptionInfo.is_free_subscription_active
                      )}
                    >
                      {subscriptionInfo.is_free_subscription_active
                        ? 'GRATUITO ACTIVO'
                        : subscriptionInfo.subscription_status.toUpperCase()}
                    </Badge>
                  </div>
                </div>

                {/* Información de Suscripción Gratuita */}
                {subscriptionInfo.free_subscription_plan && (
                  <div className="rounded-lg border border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-950/20 p-4">
                    <div className="space-y-3">
                      <div className="flex items-start gap-2">
                        <Check className="w-5 h-5 text-amber-600 dark:text-amber-400 mt-0.5" />
                        <div>
                          <p className="font-semibold text-amber-900 dark:text-amber-100">
                            Suscripción Gratuita Otorgada
                          </p>
                          <p className="text-sm text-amber-800 dark:text-amber-200 mt-1">
                            Plan:{' '}
                            <span className="font-semibold">
                              {subscriptionInfo.free_subscription_plan.toUpperCase()}
                            </span>
                          </p>
                        </div>
                      </div>

                      {subscriptionInfo.free_subscription_reason && (
                        <div className="ml-7">
                          <p className="text-sm text-amber-700 dark:text-amber-300">
                            <span className="font-semibold">Razón:</span>{' '}
                            {subscriptionInfo.free_subscription_reason}
                          </p>
                        </div>
                      )}

                      {subscriptionInfo.free_subscription_until && (
                        <div className="ml-7">
                          <p className="text-sm text-amber-700 dark:text-amber-300">
                            <span className="font-semibold">Vence:</span>{' '}
                            {new Date(subscriptionInfo.free_subscription_until).toLocaleDateString(
                              'es-ES',
                              {
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric',
                              }
                            )}
                            {subscriptionInfo.is_free_subscription_active && (
                              <span className="ml-2">✓ Activa</span>
                            )}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Acciones */}
                <div className="flex gap-2 pt-4">
                  <Dialog open={grantDialogOpen} onOpenChange={setGrantDialogOpen}>
                    <DialogTrigger asChild>
                      <Button className="bg-green-600 hover:bg-green-700">
                        <Gift className="w-4 h-4 mr-2" />
                        Otorgar Suscripción Gratuita
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Otorgar Suscripción Gratuita</DialogTitle>
                        <DialogDescription>
                          Otorga acceso gratuito PRO a {selectedTenant?.name}
                        </DialogDescription>
                      </DialogHeader>

                      <div className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="plan-select">Plan a Otorgar</Label>
                          <Select
                            value={grantFormData.plan}
                            onValueChange={(value) =>
                              setGrantFormData({ ...grantFormData, plan: value })
                            }
                          >
                            <SelectTrigger id="plan-select">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="pro">PRO - Ilimitado</SelectItem>
                              <SelectItem value="standard">ESTÁNDAR - 1,000 tickets/mes, 3 nodos</SelectItem>
                              <SelectItem value="basic">BÁSICO - 200 tickets/mes, 1 nodo</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="days-input">Duración (días)</Label>
                          <Input
                            id="days-input"
                            type="number"
                            min="1"
                            max="365"
                            value={grantFormData.days}
                            onChange={(e) =>
                              setGrantFormData({
                                ...grantFormData,
                                days: parseInt(e.target.value) || 1,
                              })
                            }
                            placeholder="30"
                          />
                          <p className="text-xs text-gray-500">
                            Máximo recomendado: 365 días (1 año)
                          </p>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="reason-input">Razón (opcional)</Label>
                          <Input
                            id="reason-input"
                            type="text"
                            value={grantFormData.reason}
                            onChange={(e) =>
                              setGrantFormData({ ...grantFormData, reason: e.target.value })
                            }
                            placeholder="ej: prueba, promoción, partnership"
                          />
                        </div>

                        <Button
                          onClick={() => grantMutation.mutate(grantFormData)}
                          disabled={grantMutation.isPending}
                          className="w-full bg-green-600 hover:bg-green-700"
                        >
                          {grantMutation.isPending ? 'Otorgando...' : 'Confirmar Suscripción'}
                        </Button>
                      </div>
                    </DialogContent>
                  </Dialog>

                  {subscriptionInfo.free_subscription_plan && (
                    <Button
                      onClick={() => {
                        if (confirm('¿Deseas revocar la suscripción gratuita?')) {
                          revokeMutation.mutate();
                        }
                      }}
                      disabled={revokeMutation.isPending}
                      variant="outline"
                      className="border-red-300 text-red-600 hover:bg-red-50 dark:hover:bg-red-950"
                    >
                      <X className="w-4 h-4 mr-2" />
                      Revocar
                    </Button>
                  )}
                </div>
              </>
            ) : null}
          </CardContent>
        </Card>
      )}

      {/* Información sobre planes */}
      <Card className="bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <AlertCircle className="w-5 h-5" />
            Información sobre Planes
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="space-y-2">
              <p className="font-semibold">PRO (Ilimitado)</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Acceso ilimitado a nodos, tickets y todas las características premium. Ideal para
                pruebas y partnerships.
              </p>
            </div>
            <div className="space-y-2">
              <p className="font-semibold">BASIC (Limitado)</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Acceso limitado: 1 nodo máximo y tickets limitados. Opción intermedia.
              </p>
            </div>
            <div className="space-y-2">
              <p className="font-semibold">FREE (Predeterminado)</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Plan gratuito con limitaciones severas. Se asigna al revocar suscripción.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminSubscriptions;
