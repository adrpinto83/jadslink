import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Check, X } from 'lucide-react';
import { SaaSPlan } from '@/types/plans';

interface PricingCardProps {
  plan: SaaSPlan;
  onSelect?: (tier: string) => void;
  currentPlan?: string;
}

/**
 * Componente reutilizable para mostrar una tarjeta de plan SaaS
 */
export const PricingCard: React.FC<PricingCardProps> = ({ plan, onSelect, currentPlan }) => {
  const isCurrentPlan = currentPlan === plan.tier;

  return (
    <Card
      className={`relative p-6 flex flex-col h-full transition-all ${
        plan.is_recommended ? 'border-2 border-purple-500 shadow-lg scale-105' : ''
      }`}
    >
      {plan.badge && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <Badge className="bg-purple-600 text-white">{plan.badge}</Badge>
        </div>
      )}

      <div className="text-center mb-6">
        <h3 className="text-2xl font-bold">{plan.name}</h3>
        <p className="text-sm text-gray-600 mt-2">{plan.description}</p>
      </div>

      <div className="text-center mb-8">
        <div className="flex items-baseline justify-center gap-1">
          <span className="text-5xl font-bold">${Number(plan.monthly_price).toFixed(0)}</span>
          <span className="text-gray-600">/mes</span>
        </div>
      </div>

      <ul className="space-y-4 mb-8 flex-grow">
        {plan.features.map((feature, idx) => (
          <li key={idx} className="flex items-start gap-3">
            {feature.included ? (
              <Check className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
            ) : (
              <X className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
            )}
            <span className={feature.included ? 'text-gray-900' : 'text-gray-400'}>{feature.text}</span>
          </li>
        ))}
      </ul>

      <Button
        onClick={() => onSelect?.(plan.tier)}
        disabled={isCurrentPlan}
        variant={plan.is_recommended ? 'default' : 'outline'}
        className="w-full"
      >
        {isCurrentPlan ? 'Plan Actual' : 'Seleccionar Plan'}
      </Button>
    </Card>
  );
};
