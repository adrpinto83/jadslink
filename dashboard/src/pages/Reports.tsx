import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import {
  DollarSign,
  TrendingUp,
  Users,
  Ticket,
  Download,
  Calendar,
  BarChart3
} from 'lucide-react';

interface Node {
  id: string;
  name: string;
}

interface Plan {
  id: string;
  name: string;
  duration_minutes: number;
  price_usd: number;
}

interface TicketData {
  id: string;
  code: string;
  status: 'pending' | 'active' | 'used' | 'expired';
  created_at: string;
  activated_at: string | null;
  node: Node | null;
  plan: Plan | null;
}

interface Session {
  id: string;
  started_at: string;
  ended_at: string | null;
  status: 'active' | 'ended' | 'expired';
  node: Node | null;
  plan: Plan | null;
}

const Reports: React.FC = () => {
  const [dateRange, setDateRange] = useState<'today' | 'week' | 'month' | 'all'>('month');

  // Fetch data
  const { data: tickets, isLoading: isLoadingTickets } = useQuery<TicketData[]>({
    queryKey: ['all-tickets'],
    queryFn: () => apiClient.get('/tickets').then(res => res.data),
  });

  const { data: sessions, isLoading: isLoadingSessions } = useQuery<Session[]>({
    queryKey: ['sessions'],
    queryFn: () => apiClient.get('/sessions').then(res => res.data),
  });

  const { data: nodes } = useQuery<Node[]>({
    queryKey: ['nodes'],
    queryFn: () => apiClient.get('/nodes').then(res => res.data)
  });

  const { data: plans } = useQuery<Plan[]>({
    queryKey: ['plans'],
    queryFn: () => apiClient.get('/plans').then(res => res.data)
  });

  // Calculate date filter
  const getFilteredData = <T extends { created_at?: string; started_at?: string }>(data: T[] | undefined): T[] => {
    if (!data) return [];

    const now = new Date();
    let startDate: Date;

    switch (dateRange) {
      case 'today':
        startDate = new Date(now.setHours(0, 0, 0, 0));
        break;
      case 'week':
        startDate = new Date(now.setDate(now.getDate() - 7));
        break;
      case 'month':
        startDate = new Date(now.setMonth(now.getMonth() - 1));
        break;
      case 'all':
      default:
        return data;
    }

    return data.filter(item => {
      const dateStr = item.created_at || item.started_at;
      if (!dateStr) return false;
      const itemDate = new Date(dateStr);
      return itemDate >= startDate;
    });
  };

  const filteredTickets = getFilteredData(tickets);
  const filteredSessions = getFilteredData(sessions);

  // Calculate statistics
  const totalRevenue = filteredTickets
    .filter(t => t.status !== 'pending')
    .reduce((sum, t) => sum + (t.plan?.price_usd || 0), 0);

  const totalTicketsSold = filteredTickets.filter(t => t.status !== 'pending').length;
  const activeSessionsCount = sessions?.filter(s => s.status === 'active').length || 0;
  const avgSessionDuration = filteredSessions.length > 0
    ? filteredSessions
        .filter(s => s.ended_at)
        .reduce((sum, s) => {
          const start = new Date(s.started_at).getTime();
          const end = new Date(s.ended_at!).getTime();
          return sum + (end - start) / 1000 / 60; // minutes
        }, 0) / filteredSessions.filter(s => s.ended_at).length
    : 0;

  // Revenue by node
  const revenueByNode = nodes?.map(node => {
    const nodeTickets = filteredTickets.filter(
      t => t.node?.id === node.id && t.status !== 'pending'
    );
    const revenue = nodeTickets.reduce((sum, t) => sum + (t.plan?.price_usd || 0), 0);
    return {
      node: node.name,
      ticketsSold: nodeTickets.length,
      revenue,
    };
  }).sort((a, b) => b.revenue - a.revenue) || [];

  // Revenue by plan
  const revenueByPlan = plans?.map(plan => {
    const planTickets = filteredTickets.filter(
      t => t.plan?.id === plan.id && t.status !== 'pending'
    );
    const revenue = planTickets.reduce((sum, t) => sum + (t.plan?.price_usd || 0), 0);
    return {
      plan: plan.name,
      ticketsSold: planTickets.length,
      revenue,
    };
  }).sort((a, b) => b.revenue - a.revenue) || [];

  const StatCard = ({
    title,
    value,
    description,
    icon: Icon,
    loading = false
  }: {
    title: string;
    value: string | number;
    description: string;
    icon: any;
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
          </>
        )}
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Reportes</h2>
          <p className="text-muted-foreground">
            Analiza el rendimiento de tu negocio
          </p>
        </div>
        <Button variant="outline" size="sm">
          <Download className="h-4 w-4 mr-2" />
          Exportar PDF
        </Button>
      </div>

      {/* Date Range Filter */}
      <Card>
        <CardHeader>
          <CardTitle>Período de Análisis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 flex-wrap">
            <Button
              variant={dateRange === 'today' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setDateRange('today')}
            >
              <Calendar className="h-4 w-4 mr-2" />
              Hoy
            </Button>
            <Button
              variant={dateRange === 'week' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setDateRange('week')}
            >
              <Calendar className="h-4 w-4 mr-2" />
              Últimos 7 días
            </Button>
            <Button
              variant={dateRange === 'month' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setDateRange('month')}
            >
              <Calendar className="h-4 w-4 mr-2" />
              Último mes
            </Button>
            <Button
              variant={dateRange === 'all' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setDateRange('all')}
            >
              <Calendar className="h-4 w-4 mr-2" />
              Todo el tiempo
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-4">
        <StatCard
          title="Ingresos Totales"
          value={`$${totalRevenue.toFixed(2)}`}
          description={`En ${dateRange === 'today' ? 'el día' : dateRange === 'week' ? 'la semana' : dateRange === 'month' ? 'el mes' : 'total'}`}
          icon={DollarSign}
          loading={isLoadingTickets}
        />
        <StatCard
          title="Tickets Vendidos"
          value={totalTicketsSold}
          description="Activados o usados"
          icon={Ticket}
          loading={isLoadingTickets}
        />
        <StatCard
          title="Sesiones Activas"
          value={activeSessionsCount}
          description="Usuarios conectados ahora"
          icon={Users}
          loading={isLoadingSessions}
        />
        <StatCard
          title="Duración Promedio"
          value={`${Math.round(avgSessionDuration)} min`}
          description="Por sesión completada"
          icon={TrendingUp}
          loading={isLoadingSessions}
        />
      </div>

      {/* Revenue by Node */}
      <Card>
        <CardHeader>
          <CardTitle>Ingresos por Nodo</CardTitle>
          <CardDescription>
            Rendimiento de cada punto de acceso
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoadingTickets ? (
            <div className="text-center py-8">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent" />
            </div>
          ) : revenueByNode.length === 0 ? (
            <p className="text-center py-8 text-muted-foreground">No hay datos disponibles</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nodo</TableHead>
                  <TableHead className="text-right">Tickets Vendidos</TableHead>
                  <TableHead className="text-right">Ingresos</TableHead>
                  <TableHead className="text-right">Promedio por Ticket</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {revenueByNode.map((item, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-medium">{item.node}</TableCell>
                    <TableCell className="text-right">{item.ticketsSold}</TableCell>
                    <TableCell className="text-right font-medium text-green-600 dark:text-green-400">
                      ${item.revenue.toFixed(2)}
                    </TableCell>
                    <TableCell className="text-right">
                      ${item.ticketsSold > 0 ? (item.revenue / item.ticketsSold).toFixed(2) : '0.00'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Revenue by Plan */}
      <Card>
        <CardHeader>
          <CardTitle>Ingresos por Plan</CardTitle>
          <CardDescription>
            Popularidad y rendimiento de cada plan
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoadingTickets ? (
            <div className="text-center py-8">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent" />
            </div>
          ) : revenueByPlan.length === 0 ? (
            <p className="text-center py-8 text-muted-foreground">No hay datos disponibles</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Plan</TableHead>
                  <TableHead className="text-right">Tickets Vendidos</TableHead>
                  <TableHead className="text-right">Ingresos</TableHead>
                  <TableHead className="text-right">% del Total</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {revenueByPlan.map((item, index) => {
                  const percentage = totalRevenue > 0 ? (item.revenue / totalRevenue) * 100 : 0;
                  return (
                    <TableRow key={index}>
                      <TableCell className="font-medium">{item.plan}</TableCell>
                      <TableCell className="text-right">{item.ticketsSold}</TableCell>
                      <TableCell className="text-right font-medium text-green-600 dark:text-green-400">
                        ${item.revenue.toFixed(2)}
                      </TableCell>
                      <TableCell className="text-right">{percentage.toFixed(1)}%</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Charts placeholder - will add once recharts is installed */}
      <Card>
        <CardHeader>
          <CardTitle>Gráficos de Rendimiento</CardTitle>
          <CardDescription>
            Visualización de tendencias y métricas
          </CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center">
            <BarChart3 className="mx-auto h-12 w-12 text-muted-foreground" />
            <p className="mt-4 text-lg font-medium">Gráficos próximamente</p>
            <p className="text-sm text-muted-foreground">
              Los gráficos interactivos se agregarán en la próxima actualización
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Reports;
