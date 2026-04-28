import React from 'react';
import { useQuery } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  Activity,
  Users,
  Ticket,
  Wifi,
  TrendingUp,
  MapPin,
  Clock,
  DollarSign
} from 'lucide-react';

interface DashboardStats {
  total_nodes: number;
  online_nodes: number;
  total_plans: number;
  total_tickets: number;
  active_tickets: number;
  pending_tickets: number;
  active_sessions: number;
  total_revenue: number;
}



const Dashboard: React.FC = () => {
  const { data: stats, isLoading: loadingStats } = useQuery<DashboardStats>({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      // Fetch all data in parallel
      const [nodes, plans, tickets, sessions] = await Promise.all([
        apiClient.get('/nodes').then(res => res.data),
        apiClient.get('/plans').then(res => res.data),
        apiClient.get('/tickets').then(res => res.data),
        apiClient.get('/sessions').then(res => res.data),
      ]);

      // Calculate stats
      const onlineNodes = nodes.filter((n: any) => n.status === 'online').length;
      const activeTickets = tickets.filter((t: any) => t.status === 'active').length;
      const pendingTickets = tickets.filter((t: any) => t.status === 'pending').length;
      const activeSessions = sessions.filter((s: any) => s.status === 'active').length;

      // Calculate revenue (sum of activated tickets)
      const revenue = tickets
        .filter((t: any) => t.status !== 'pending')
        .reduce((sum: number, t: any) => sum + (t.plan?.price_usd || 0), 0);

      return {
        total_nodes: nodes.length,
        online_nodes: onlineNodes,
        total_plans: plans.length,
        total_tickets: tickets.length,
        active_tickets: activeTickets,
        pending_tickets: pendingTickets,
        active_sessions: activeSessions,
        total_revenue: revenue,
      };
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const StatCard = ({
    title,
    value,
    description,
    icon: Icon,
    trend,
    loading = false
  }: {
    title: string;
    value: string | number;
    description: string;
    icon: any;
    trend?: string;
    loading?: boolean;
  }) => (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="h-7 w-20 bg-muted animate-pulse rounded" />
        ) : (
          <>
            <div className="text-2xl font-bold">{value}</div>
            <p className="text-xs text-muted-foreground">{description}</p>
            {trend && (
              <div className="flex items-center mt-2 text-xs text-green-600 dark:text-green-400">
                <TrendingUp className="h-3 w-3 mr-1" />
                {trend}
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">
          Vista general de tu operación
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Nodos Activos"
          value={loadingStats ? "..." : `${stats?.online_nodes || 0}/${stats?.total_nodes || 0}`}
          description="Nodos online / Total"
          icon={Wifi}
          loading={loadingStats}
        />
        <StatCard
          title="Sesiones Activas"
          value={loadingStats ? "..." : stats?.active_sessions || 0}
          description="Usuarios conectados ahora"
          icon={Users}
          loading={loadingStats}
        />
        <StatCard
          title="Tickets Generados"
          value={loadingStats ? "..." : stats?.total_tickets || 0}
          description={`${stats?.pending_tickets || 0} pendientes`}
          icon={Ticket}
          loading={loadingStats}
        />
        <StatCard
          title="Ingresos Totales"
          value={loadingStats ? "..." : `$${stats?.total_revenue?.toFixed(2) || '0.00'}`}
          description="Por tickets vendidos"
          icon={DollarSign}
          loading={loadingStats}
        />
      </div>

      {/* Secondary Stats */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Resumen de Operación</CardTitle>
            <CardDescription>Métricas principales de tu red</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <MapPin className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">Nodos Totales</span>
              </div>
              <span className="font-bold">{stats?.total_nodes || 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Activity className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">Nodos Online</span>
              </div>
              <span className="font-bold text-green-600">{stats?.online_nodes || 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Ticket className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">Planes Activos</span>
              </div>
              <span className="font-bold">{stats?.total_plans || 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">Tickets Activos</span>
              </div>
              <span className="font-bold text-blue-600">{stats?.active_tickets || 0}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Estado de la Red</CardTitle>
            <CardDescription>Información en tiempo real</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Online Nodes Percentage */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">Disponibilidad de Nodos</span>
                  <span className="text-sm text-muted-foreground">
                    {stats?.total_nodes ?
                      Math.round((stats.online_nodes / stats.total_nodes) * 100) : 0}%
                  </span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div
                    className="bg-green-600 h-2 rounded-full transition-all"
                    style={{
                      width: `${stats?.total_nodes ?
                        (stats.online_nodes / stats.total_nodes) * 100 : 0}%`
                    }}
                  />
                </div>
              </div>

              {/* Active Sessions */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">Sesiones Activas</span>
                  <span className="text-sm text-muted-foreground">
                    {stats?.active_sessions || 0} usuarios
                  </span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{
                      width: `${Math.min((stats?.active_sessions || 0) * 10, 100)}%`
                    }}
                  />
                </div>
              </div>

              {/* Ticket Usage */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">Uso de Tickets</span>
                  <span className="text-sm text-muted-foreground">
                    {stats?.active_tickets || 0} / {stats?.total_tickets || 0}
                  </span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div
                    className="bg-purple-600 h-2 rounded-full transition-all"
                    style={{
                      width: `${stats?.total_tickets ?
                        (stats.active_tickets / stats.total_tickets) * 100 : 0}%`
                    }}
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Acciones Rápidas</CardTitle>
          <CardDescription>Accede a las funciones más utilizadas</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <a
              href="/dashboard/tickets"
              className="flex flex-col items-center justify-center p-4 border rounded-lg hover:bg-accent hover:text-accent-foreground transition-colors cursor-pointer"
            >
              <Ticket className="h-8 w-8 mb-2" />
              <span className="text-sm font-medium">Generar Tickets</span>
            </a>
            <a
              href="/dashboard/nodes"
              className="flex flex-col items-center justify-center p-4 border rounded-lg hover:bg-accent hover:text-accent-foreground transition-colors cursor-pointer"
            >
              <MapPin className="h-8 w-8 mb-2" />
              <span className="text-sm font-medium">Ver Nodos</span>
            </a>
            <a
              href="/dashboard/sessions"
              className="flex flex-col items-center justify-center p-4 border rounded-lg hover:bg-accent hover:text-accent-foreground transition-colors cursor-pointer"
            >
              <Users className="h-8 w-8 mb-2" />
              <span className="text-sm font-medium">Sesiones</span>
            </a>
            <a
              href="/dashboard/reports"
              className="flex flex-col items-center justify-center p-4 border rounded-lg hover:bg-accent hover:text-accent-foreground transition-colors cursor-pointer"
            >
              <Activity className="h-8 w-8 mb-2" />
              <span className="text-sm font-medium">Reportes</span>
            </a>
          </div>
        </CardContent>
      </Card>

    </div>
  );
};

export default Dashboard;
