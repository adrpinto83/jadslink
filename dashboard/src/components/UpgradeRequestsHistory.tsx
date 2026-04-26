import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, CheckCircle2, Clock, XCircle } from 'lucide-react';

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

interface UpgradeRequestsHistoryProps {
  requests: UpgradeRequest[];
  isLoading?: boolean;
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'approved':
      return <CheckCircle2 className="w-5 h-5 text-green-600" />;
    case 'rejected':
      return <XCircle className="w-5 h-5 text-red-600" />;
    case 'pending_payment':
    case 'payment_received':
      return <Clock className="w-5 h-5 text-yellow-600" />;
    default:
      return <AlertCircle className="w-5 h-5 text-gray-600" />;
  }
};

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    pending_payment: 'Pendiente de Pago',
    payment_received: 'Pago Recibido',
    approved: 'Aprobado',
    rejected: 'Rechazado',
    cancelled: 'Cancelado',
  };
  return labels[status] || status;
};

const getStatusColor = (status: string) => {
  switch (status) {
    case 'approved':
      return 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-200';
    case 'rejected':
      return 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200';
    case 'pending_payment':
    case 'payment_received':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-950 dark:text-yellow-200';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-950 dark:text-gray-200';
  }
};

const getUpgradeDescription = (request: UpgradeRequest) => {
  if (request.upgrade_type === 'extra_tickets') {
    return `Compra de ${request.ticket_quantity} tickets adicionales`;
  }
  return `Upgrade a Plan ${request.new_plan_tier?.charAt(0).toUpperCase()}${request.new_plan_tier?.slice(1)}`;
};

export const UpgradeRequestsHistory: React.FC<UpgradeRequestsHistoryProps> = ({
  requests,
  isLoading = false,
}) => {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Historial de Solicitudes</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  if (requests.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Historial de Solicitudes</CardTitle>
          <CardDescription>Sin solicitudes de pago o upgrade</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <AlertCircle className="w-12 h-12 mx-auto text-gray-400 mb-3" />
            <p className="text-gray-500">No tienes solicitudes aún</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Historial de Solicitudes</CardTitle>
        <CardDescription>Tus solicitudes de pago y upgrades</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {requests.map((request) => (
            <div
              key={request.id}
              className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3 flex-1">
                  {getStatusIcon(request.status)}
                  <div className="flex-1">
                    <p className="font-semibold text-gray-900 dark:text-white">
                      {getUpgradeDescription(request)}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {request.payment_method === 'pago_movil' ? (
                        <>
                          💳 Pago Móvil • Banco: {request.banco_origen || 'N/A'} •{' '}
                          {request.referencia_pago ? (
                            <span className="font-mono">Ref: {request.referencia_pago}</span>
                          ) : (
                            'Sin referencia'
                          )}
                        </>
                      ) : (
                        '💳 Tarjeta (en desarrollo)'
                      )}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(request.created_at).toLocaleDateString('es-VE', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
                  </div>
                </div>

                <div className="text-right space-y-2">
                  <div>
                    <p className="text-lg font-bold text-gray-900 dark:text-white">
                      ${request.amount_usd.toFixed(2)}
                    </p>
                    <p className="text-xs text-gray-500">
                      ≈ Bs. {request.amount_vef?.toFixed(2) || 'N/A'}
                    </p>
                  </div>
                  <Badge className={`${getStatusColor(request.status)}`}>
                    {getStatusLabel(request.status)}
                  </Badge>
                  {request.reminder_count > 0 && (
                    <p className="text-xs text-yellow-600">
                      {request.reminder_count} recordatorio(s)
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
