/**
 * Tipos para panel de administración (superadmin)
 */

// ============================================================================
// ESTADÍSTICAS GLOBALES
// ============================================================================

export interface PlanCount {
  plan: string;
  count: number;
}

export interface NodeStatusCount {
  status: string;
  count: number;
}

export interface GlobalStats {
  total_tenants: number;
  active_tenants: number;
  inactive_tenants: number;

  total_nodes: number;
  online_nodes: number;
  offline_nodes: number;
  degraded_nodes: number;

  total_tickets: number;
  pending_tickets: number;
  active_tickets: number;
  expired_tickets: number;
  revoked_tickets: number;

  active_sessions: number;
  total_revenue_estimate: number;

  tenants_by_plan: PlanCount[];
  nodes_by_status: NodeStatusCount[];
}

// ============================================================================
// ESTADÍSTICAS POR TENANT
// ============================================================================

export interface TenantStats {
  tenant_id: string;
  tenant_name: string;
  tenant_slug: string;
  plan_tier: string;
  is_active: boolean;
  subscription_status: string;

  nodes_total: number;
  nodes_online: number;
  nodes_offline: number;
  nodes_degraded: number;

  tickets_total: number;
  tickets_pending: number;
  tickets_active: number;
  tickets_expired: number;
  tickets_revoked: number;

  sessions_active: number;
  revenue_estimate: number;
}

export interface TenantDetail {
  id: string;
  name: string;
  slug: string;
  plan_tier: string;
  subscription_status: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;

  nodes_count: number;
  tickets_count: number;
  sessions_count: number;
  users_count: number;
}

// ============================================================================
// RECURSOS DEL TENANT
// ============================================================================

export interface NodeAdmin {
  id: string;
  name: string;
  serial: string;
  status: 'online' | 'offline' | 'degraded';
  last_seen_at: string | null;
  location: {
    lat: number | null;
    lng: number | null;
    address: string;
    description?: string;
  } | null;
  wan_ip: string | null;
}

export interface TicketAdmin {
  id: string;
  code: string;
  status: 'pending' | 'active' | 'expired' | 'revoked';
  created_at: string;
  activated_at: string | null;
  expires_at: string | null;
  plan_name: string | null;
  node_name: string | null;
  device_mac: string | null;
}

export interface TicketsListResponse {
  tickets: TicketAdmin[];
  total: number;
  page: number;
  pages: number;
}

export interface SessionAdmin {
  id: string;
  ticket_id: string;
  device_mac: string;
  ip_address: string | null;
  started_at: string;
  expires_at: string;
  is_active: boolean;
  bytes_down: number;
  bytes_up: number;
  node_name: string | null;
}

// ============================================================================
// UI HELPERS
// ============================================================================

export interface StatCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: React.ComponentType<{ className?: string }>;
  trend?: {
    value: number;
    isPositive: boolean;
  };
}
