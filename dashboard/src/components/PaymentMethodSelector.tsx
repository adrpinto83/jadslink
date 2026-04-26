import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Smartphone, CreditCard } from 'lucide-react';

interface PaymentMethodSelectorProps {
  selected: 'pago_movil' | 'card' | null;
  onSelect: (method: 'pago_movil' | 'card') => void;
}

export const PaymentMethodSelector: React.FC<PaymentMethodSelectorProps> = ({
  selected,
  onSelect,
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* PAGO MÓVIL */}
      <Card
        className={`cursor-pointer transition-all ${
          selected === 'pago_movil'
            ? 'ring-2 ring-blue-500 bg-blue-50 dark:bg-blue-950'
            : 'hover:border-blue-300'
        }`}
        onClick={() => onSelect('pago_movil')}
      >
        <CardHeader>
          <div className="flex items-center gap-3">
            <Smartphone className="w-6 h-6 text-blue-600" />
            <div>
              <CardTitle className="text-lg">Pago Móvil</CardTitle>
              <CardDescription>Transferencia bancaria</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm text-gray-600 dark:text-gray-300">
            <p>✓ Soporta: BDO, Banesco, Provincial, Mercantil</p>
            <p>✓ Tasa oficial aplicada automáticamente</p>
            <p>✓ Confirmación manual del admin (24-48h)</p>
          </div>
          {selected === 'pago_movil' && (
            <Button className="mt-4 w-full" size="sm">
              Seleccionado ✓
            </Button>
          )}
        </CardContent>
      </Card>

      {/* TARJETA */}
      <Card
        className={`cursor-pointer transition-all ${
          selected === 'card'
            ? 'ring-2 ring-green-500 bg-green-50 dark:bg-green-950'
            : 'hover:border-green-300'
        }`}
        onClick={() => onSelect('card')}
      >
        <CardHeader>
          <div className="flex items-center gap-3">
            <CreditCard className="w-6 h-6 text-green-600" />
            <div>
              <CardTitle className="text-lg">Tarjeta</CardTitle>
              <CardDescription>Visa, Mastercard</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm text-gray-600 dark:text-gray-300">
            <p>✓ Procesamiento seguro con Stripe</p>
            <p>✓ Confirmación automática</p>
            <p>✓ Disponible en breve (en desarrollo)</p>
          </div>
          <Button className="mt-4 w-full" size="sm" disabled>
            En desarrollo
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};
