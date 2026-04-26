import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Zap, TrendingUp, Rocket } from 'lucide-react';

interface UpgradeOption {
  type: 'extra_tickets' | 'plan_basic' | 'plan_pro';
  title: string;
  description: string;
  price: number;
  currency: string;
  features: string[];
  icon: React.ReactNode;
  highlighted?: boolean;
  disabled?: boolean;
  disabledReason?: string;
}

interface PricingConfig {
  ticket_pack_size: number;
  ticket_pack_price_usd: string | number;
  additional_node_price_usd: string | number;
}

interface UpgradeOptionsProps {
  currentPlan?: 'free' | 'basic' | 'pro';
  ticketsAvailable?: number;
  ticketsUsed?: number;
  onSelect: (type: 'extra_tickets' | 'plan_basic' | 'plan_pro') => void;
  isLoading?: boolean;
  pricingConfig?: PricingConfig;
}

export const UpgradeOptions: React.FC<UpgradeOptionsProps> = ({
  currentPlan = 'free',
  ticketsAvailable = 50,
  ticketsUsed = 0,
  onSelect,
  isLoading = false,
  pricingConfig,
}) => {
  // Obtener precios del config o usar defaults
  const ticketPackPrice = Number(pricingConfig?.ticket_pack_price_usd || 0.5);
  const additionalNodePrice = Number(pricingConfig?.additional_node_price_usd || 29);

  const options: UpgradeOption[] = [
    {
      type: 'extra_tickets',
      title: `Comprar ${pricingConfig?.ticket_pack_size || 50} Tickets`,
      description: 'Pago por uso - Solo cuando los necesites',
      price: ticketPackPrice,
      currency: 'USD',
      features: [`${pricingConfig?.ticket_pack_size || 50} tickets adicionales`, 'Pago único', 'Sin suscripción mensual', 'Tasa oficial aplicada'],
      icon: <Zap className="w-6 h-6" />,
      disabled: ticketsAvailable > 0 && currentPlan === 'free',
      disabledReason: 'Aún tienes tickets disponibles',
    },
    {
      type: 'plan_basic',
      title: 'Plan Básico',
      description: 'Para empresas en crecimiento',
      price: additionalNodePrice,
      currency: 'USD/mes',
      features: ['1 nodo máximo', '50 tickets gratis + pago por uso', 'Soporte por email', 'Tasa oficial'],
      icon: <TrendingUp className="w-6 h-6" />,
      highlighted: currentPlan === 'free',
      disabled: currentPlan === 'basic' || currentPlan === 'pro',
      disabledReason: currentPlan === 'basic' ? 'Ya estás en este plan' : 'Debes downgrade primero',
    },
    {
      type: 'plan_pro',
      title: 'Plan Pro',
      description: 'Ilimitado - Para empresas grandes',
      price: additionalNodePrice * 2,
      currency: 'USD/mes',
      features: ['Nodos ilimitados', 'Tickets ilimitados', 'API pública', 'Soporte 24/7'],
      icon: <Rocket className="w-6 h-6" />,
      highlighted: true,
      disabled: currentPlan === 'pro',
      disabledReason: 'Ya estás en el plan máximo',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {options.map((option) => (
        <Card
          key={option.type}
          className={`flex flex-col transition-all ${
            option.highlighted
              ? 'ring-2 ring-yellow-400 shadow-xl scale-105'
              : ''
          } ${option.disabled ? 'opacity-60' : ''}`}
        >
          {option.highlighted && (
            <div className="bg-gradient-to-r from-yellow-400 to-orange-400 px-4 py-1">
              <Badge className="bg-yellow-600 text-white">⭐ RECOMENDADO</Badge>
            </div>
          )}

          <CardHeader>
            <div className="flex items-start justify-between mb-2">
              <div className="text-yellow-600 dark:text-yellow-400">{option.icon}</div>
              {option.disabled && (
                <Badge variant="secondary" className="text-xs">
                  No disponible
                </Badge>
              )}
            </div>
            <CardTitle className="text-lg">{option.title}</CardTitle>
            <CardDescription>{option.description}</CardDescription>
          </CardHeader>

          <CardContent className="flex-1 flex flex-col space-y-4">
            {/* PRECIO */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950 dark:to-indigo-950 p-3 rounded-lg">
              <p className="text-3xl font-bold text-blue-600">
                ${option.price.toFixed(2)}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">{option.currency}</p>
            </div>

            {/* FEATURES */}
            <ul className="space-y-2 flex-1">
              {option.features.map((feature, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm">
                  <span className="text-green-600 mt-0.5">✓</span>
                  <span className="text-gray-700 dark:text-gray-300">{feature}</span>
                </li>
              ))}
            </ul>

            {/* BOTÓN */}
            <Button
              onClick={() => onSelect(option.type)}
              disabled={option.disabled || isLoading}
              className={`w-full mt-4 ${
                option.highlighted
                  ? 'bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600'
                  : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700'
              }`}
            >
              {option.disabled ? (
                <span className="text-sm">{option.disabledReason}</span>
              ) : isLoading ? (
                'Procesando...'
              ) : option.type === 'extra_tickets' ? (
                'Comprar'
              ) : (
                'Actualizar'
              )}
            </Button>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};
