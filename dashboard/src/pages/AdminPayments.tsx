import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AdminPaymentConfirm } from '@/components/AdminPaymentConfirm';
import { AlertCircle, DollarSign, TrendingUp, CheckCircle2 } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface PendingPayment {
  id: string;
  tenant_name: string;
  contact_email: string;
  upgrade_type: 'extra_tickets' | 'plan_upgrade';
  amount_usd: number;
  amount_vef: number;
  exchange_rate: number;
  payment_method: 'pago_movil' | 'card';
  status: 'pending_payment' | 'payment_received';
  banco_origen?: string;
  referencia_pago?: string;
  comprobante_url?: string;
  created_at: string;
  days_pending: number;
  reminder_count: number;
  ticket_quantity?: number;
  new_plan_tier?: string;
}

interface PaymentHistoryItem {
  id: string;
  tenant_name: string;
  contact_email: string;
  upgrade_type: 'extra_tickets' | 'plan_upgrade';
  amount_usd: number;
  amount_vef: number;
  status: 'pending_payment' | 'payment_received' | 'approved' | 'rejected' | 'cancelled';
  banco_origen?: string;
  referencia_pago?: string;
  created_at: string;
  days_pending: number;
  approved_by?: string;
  admin_notes?: string;
  ticket_quantity?: number;
  new_plan_tier?: string;
}

const AdminPayments: React.FC = () => {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<'pending' | 'all'>('pending');

  const { data: pendingPayments = [], isLoading: isLoadingPending, refetch: refetchPending } = useQuery<PendingPayment[]>({
    queryKey: ['admin', 'pending-payments'],
    queryFn: async () => {
      const response = await apiClient.get('/subscriptions/admin/pending-payments');
      return response.data;
    },
    refetchInterval: 30000, // Refetch cada 30 segundos
  });

  const { data: paymentHistory = [], isLoading: isLoadingHistory } = useQuery<PaymentHistoryItem[]>({
    queryKey: ['admin', 'payment-history', statusFilter],
    queryFn: async () => {
      const response = await apiClient.get('/subscriptions/admin/payment-history', {
        params: {
          status_filter: statusFilter === 'pending' ? 'pending_payment' : undefined,
          limit: 100,
        },
      });
      return response.data;
    },
  });

  const handlePaymentConfirmed = () => {
    refetchPending();
    queryClient.invalidateQueries({ queryKey: ['admin', 'payment-history'] });
  };

  const totalPendingUSD = pendingPayments.reduce((sum, p) => sum + p.amount_usd, 0);
  const totalPendingVEF = pendingPayments.reduce((sum, p) => sum + p.amount_vef, 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Gestión de Pagos</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Revisa y confirma solicitudes de pago de clientes
        </p>
      </div>

      {/* Resumen de Pagos Pendientes */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-600 dark:text-gray-400">Solicitudes Pendientes</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{pendingPayments.length}</p>
            <p className="text-xs text-gray-500 mt-1">Requieren confirmación</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-600 dark:text-gray-400">Monto Total Pendiente</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">${totalPendingUSD.toFixed(2)}</p>
            <p className="text-xs text-gray-500 mt-1">≈ Bs. {totalPendingVEF.toFixed(2)}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-gray-600 dark:text-gray-400">Solicitudes Muy Antiguas</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-orange-600">
              {pendingPayments.filter(p => p.days_pending >= 7).length}
            </p>
            <p className="text-xs text-gray-500 mt-1">(7+ días pendiente)</p>
          </CardContent>
        </Card>
      </div>

      {/* Alerta si hay muchos pagos pendientes */}
      {pendingPayments.length > 0 && (
        <Alert className="bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
          <AlertCircle className="h-4 w-4 text-blue-600" />
          <AlertDescription className="text-blue-800 dark:text-blue-200">
            Tienes {pendingPayments.length} solicitud(es) de pago esperando confirmación.
            {pendingPayments.filter(p => p.days_pending >= 14).length > 0 && (
              <span className="block mt-1">
                ⚠️ {pendingPayments.filter(p => p.days_pending >= 14).length} de ellas llevan más de 14 días pendiente.
              </span>
            )}
          </AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="pending" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="pending">
            Pendientes ({pendingPayments.length})
          </TabsTrigger>
          <TabsTrigger value="historial">Historial Completo</TabsTrigger>
        </TabsList>

        {/* Tab: Pagos Pendientes */}
        <TabsContent value="pending" className="space-y-4">
          {isLoadingPending ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-64 w-full" />
              ))}
            </div>
          ) : pendingPayments.length === 0 ? (
            <Card className="p-6 text-center">
              <CheckCircle2 className="w-12 h-12 mx-auto text-green-600 mb-3" />
              <h3 className="font-semibold text-lg mb-1">¡Todo Procesado!</h3>
              <p className="text-gray-600 dark:text-gray-400">
                No hay solicitudes de pago pendientes de confirmación.
              </p>
            </Card>
          ) : (
            <div className="space-y-4">
              {pendingPayments.map((payment) => (
                <AdminPaymentConfirm
                  key={payment.id}
                  payment={payment}
                  onConfirmSuccess={handlePaymentConfirmed}
                />
              ))}
            </div>
          )}
        </TabsContent>

        {/* Tab: Historial Completo */}
        <TabsContent value="historial" className="space-y-4">
          <div className="flex gap-2 mb-4">
            <Button
              variant={statusFilter === 'pending' ? 'default' : 'outline'}
              onClick={() => setStatusFilter('pending')}
            >
              Solo Pendientes
            </Button>
            <Button
              variant={statusFilter === 'all' ? 'default' : 'outline'}
              onClick={() => setStatusFilter('all')}
            >
              Todos
            </Button>
          </div>

          {isLoadingHistory ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-24 w-full" />
              ))}
            </div>
          ) : paymentHistory.length === 0 ? (
            <Card className="p-6 text-center">
              <AlertCircle className="w-12 h-12 mx-auto text-gray-400 mb-3" />
              <p className="text-gray-600 dark:text-gray-400">
                No hay solicitudes de pago en el historial.
              </p>
            </Card>
          ) : (
            <div className="space-y-4">
              {paymentHistory.map((item) => (
                <Card key={item.id} className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold">{item.tenant_name}</h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{item.contact_email}</p>
                      <p className="text-sm mt-2">
                        {item.upgrade_type === 'extra_tickets'
                          ? `Compra de 50 tickets`
                          : `Upgrade a Plan ${item.new_plan_tier?.charAt(0).toUpperCase()}${item.new_plan_tier?.slice(1)}`}
                      </p>
                    </div>

                    <div className="text-right space-y-2">
                      <div>
                        <p className="font-semibold">${item.amount_usd.toFixed(2)}</p>
                        <p className="text-xs text-gray-500">≈ Bs. {item.amount_vef.toFixed(2)}</p>
                      </div>
                      <Badge
                        variant={
                          item.status === 'approved'
                            ? 'default'
                            : item.status === 'rejected'
                            ? 'destructive'
                            : 'secondary'
                        }
                      >
                        {item.status === 'approved'
                          ? 'Aprobado'
                          : item.status === 'rejected'
                          ? 'Rechazado'
                          : item.status === 'cancelled'
                          ? 'Cancelado'
                          : 'Pendiente'}
                      </Badge>
                    </div>
                  </div>

                  {item.admin_notes && (
                    <div className="mt-3 p-2 bg-gray-50 dark:bg-gray-900 rounded text-sm">
                      <p className="text-gray-600 dark:text-gray-400">Notas: {item.admin_notes}</p>
                      {item.approved_by && (
                        <p className="text-xs text-gray-500 mt-1">Por: {item.approved_by}</p>
                      )}
                    </div>
                  )}

                  <p className="text-xs text-gray-500 mt-2">
                    {new Date(item.created_at).toLocaleDateString('es-VE', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AdminPayments;
