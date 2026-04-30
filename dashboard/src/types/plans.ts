/**
 * Tipos para planes SaaS
 */

export interface PlanFeature {
  icon: string;
  text: string;
  included: boolean;
}

export interface SaaSPlan {
  // Identificación
  tier: 'free' | 'basic' | 'standard' | 'pro';
  name: string;
  description: string;

  // Precios
  monthly_price: number;
  monthly_price_display: string;

  // Tickets
  included_tickets: number;
  additional_tickets_price: number | null;
  additional_tickets_display: string;
  is_tickets_unlimited: boolean;

  // Nodos
  included_nodes: number;
  additional_node_price: number | null;
  additional_node_display: string;
  is_nodes_unlimited: boolean;

  // Features
  features: PlanFeature[];
  support_level: string;
  has_api_access: boolean;
  reports_level: string;
  data_retention: string;

  // UI
  icon: string;
  color: string;
  is_recommended: boolean;
  badge: string | null;
}
