import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, CheckCircle2, XCircle } from 'lucide-react';
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

interface AdminPaymentConfirmProps {
  payment: PendingPayment;
  onConfirmSuccess?: () => void;
}

export const AdminPaymentConfirm: React.FC<AdminPaymentConfirmProps> = ({
  payment,
  onConfirmSuccess,
}) => {
  const [adminNotes, setAdminNotes] = useState('');
  const [action, setAction] = useState<'approve' | 'reject' | null>(null);

  const confirmMutation = useMutation({
    mutationFn: async (confirmAction: 'approve' | 'reject') => {
      const response = await apiClient.post(
        `/subscriptions/admin/confirm-payment/${payment.id}`,
        {
          action: confirmAction,
          notes: adminNotes,
        }
      );
      return response.data;
    },
    onSuccess: () => {
      setAdminNotes('');
      setAction(null);
      onConfirmSuccess?.();
    },
  });

  const handleApprove = () => {
    setAction('approve');
    confirmMutation.mutate('approve');
  };

  const handleReject = () => {
    setAction('reject');
    confirmMutation.mutate('reject');
  };

  const getUpgradeDescription = () => {
    if (payment.upgrade_type === 'extra_tickets') {
      return `Compra de ${payment.ticket_quantity} tickets adicionales`;
    }
    return `Upgrade a Plan ${payment.new_plan_tier?.charAt(0).toUpperCase()}${payment.new_plan_tier?.slice(1)}`;
  };

  const getDaysColor = (days: number) => {
    if (days >= 14) return 'text-red-600 dark:text-red-400';
    if (days >= 7) return 'text-orange-600 dark:text-orange-400';
    return 'text-yellow-600 dark:text-yellow-400';
  };

  return (
    <Card className="border-blue-200 dark:border-blue-800">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg">{payment.tenant_name}</CardTitle>
            <CardDescription>{payment.contact_email}</CardDescription>
          </div>
          <Badge variant="secondary">{payment.days_pending}d pendiente</Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Información del Pago */}
        <div className="grid grid-cols-2 gap-4 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
          <div>
            <p className="text-xs text-gray-600 dark:text-gray-400">Solicitud</p>
            <p className="font-semibold">{getUpgradeDescription()}</p>
          </div>
          <div>
            <p className="text-xs text-gray-600 dark:text-gray-400">Monto</p>
            <p className="font-semibold">
              ${payment.amount_usd.toFixed(2)} USD
              <br />
              <span className="text-sm">≈ Bs. {payment.amount_vef.toFixed(2)}</span>
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-600 dark:text-gray-400">Método</p>
            <p className="font-semibold">
              {payment.payment_method === 'pago_movil' ? '💳 Pago Móvil' : '🎫 Tarjeta'}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-600 dark:text-gray-400">Tasa Oficial</p>
            <p className="font-semibold">1 USD = {payment.exchange_rate} VEF</p>
          </div>
        </div>

        {/* Detalles Pago Móvil */}
        {payment.payment_method === 'pago_movil' && (
          <div className="space-y-2 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <p className="font-semibold text-sm">Detalles de Pago Móvil</p>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <p className="text-gray-600 dark:text-gray-400">Banco</p>
                <p className="font-mono font-semibold">{payment.banco_origen || 'N/A'}</p>
              </div>
              <div>
                <p className="text-gray-600 dark:text-gray-400">Referencia</p>
                <p className="font-mono font-semibold">{payment.referencia_pago || 'N/A'}</p>
              </div>
            </div>
            {payment.comprobante_url && (
              <a
                href={payment.comprobante_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 dark:text-blue-400 hover:underline text-sm mt-2 block"
              >
                Ver Comprobante →
              </a>
            )}
          </div>
        )}

        {/* Advertencia si está muy pendiente */}
        {payment.days_pending >= 7 && (
          <Alert className="bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800">
            <AlertCircle className="h-4 w-4 text-orange-600" />
            <AlertDescription className="text-orange-800 dark:text-orange-200">
              ⚠️ Esta solicitud lleva {payment.days_pending} días pendiente.
              {payment.reminder_count > 0 && ` Se han enviado ${payment.reminder_count} recordatorio(s).`}
            </AlertDescription>
          </Alert>
        )}

        {/* Campo de Notas */}
        <div className="space-y-2">
          <label className="block text-sm font-semibold">Notas de Auditoría</label>
          <textarea
            placeholder="Ej: Pago verificado en cuenta BDO. Referencia confirmada."
            value={adminNotes}
            onChange={(e) => setAdminNotes(e.target.value)}
            rows={3}
            disabled={confirmMutation.isPending}
            className="resize-none w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          />
          <p className="text-xs text-gray-500">Estas notas se guardarán en el registro del pago</p>
        </div>

        {/* Botones de Acción */}
        <div className="flex gap-3 pt-2">
          <Button
            onClick={handleApprove}
            disabled={confirmMutation.isPending}
            className="flex-1 bg-green-600 hover:bg-green-700"
          >
            {confirmMutation.isPending && action === 'approve' ? (
              'Aprobando...'
            ) : (
              <>
                <CheckCircle2 className="w-4 h-4 mr-2" />
                Aprobar Pago
              </>
            )}
          </Button>

          <Button
            onClick={handleReject}
            disabled={confirmMutation.isPending}
            variant="destructive"
            className="flex-1"
          >
            {confirmMutation.isPending && action === 'reject' ? (
              'Rechazando...'
            ) : (
              <>
                <XCircle className="w-4 h-4 mr-2" />
                Rechazar
              </>
            )}
          </Button>
        </div>

        {confirmMutation.error && (
          <Alert className="bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800">
            <AlertCircle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800 dark:text-red-200">
              Error: {(confirmMutation.error as any)?.response?.data?.detail || 'No se pudo procesar la solicitud'}
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};
