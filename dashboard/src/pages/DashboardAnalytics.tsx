import React from 'react';
import { useQuery } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { TrendingUp, TrendingDown, Activity, Zap } from 'lucide-react';

interface AnalyticsData {
  tickets_by_day: Array<{ date: string; count: number }>;
  sessions_by_plan: Array<{ plan: string; count: number }>;
  nodes_status: Array<{ status: string; count: number }>;
  revenue_trend: Array<{ date: string; revenue: number }>;
}

const DashboardAnalytics: React.FC = () => {
  const { data: analytics, isLoading } = useQuery<AnalyticsData>({
    queryKey: ['analytics-data'],
    queryFn: async () => {
      // Generate mock data for demo
      const days = Array.from({ length: 7 }, (_, i) => {
        const d = new Date();
        d.setDate(d.getDate() - (6 - i));
        return d.toISOString().split('T')[0];
      });

      return {
        tickets_by_day: days.map(date => ({
          date: date.split('-').slice(1).join('/'),
          count: Math.floor(Math.random() * 150) + 20
        })),
        sessions_by_plan: [
          { plan: 'Free', count: 45 },
          { plan: 'Pro', count: 120 },
          { plan: 'Enterprise', count: 35 }
        ],
        nodes_status: [
          { status: 'Online', count: 14 },
          { status: 'Offline', count: 2 },
          { status: 'Maintenance', count: 1 }
        ],
        revenue_trend: days.map(date => ({
          date: date.split('-').slice(1).join('/'),
          revenue: Math.floor(Math.random() * 5000) + 500
        }))
      };
    },
    refetchInterval: 60000,
  });

  if (isLoading) {
    return <div className="animate-pulse">Cargando analytics...</div>;
  }

  const COLORS = ['#3b82f6', '#ef4444', '#10b981'];

  return (
    <div className="space-y-8">
      <div className="animate-in fade-in duration-500">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">Analytics</h1>
        <p className="text-gray-600 mt-2">Última actualización: hace 1 minuto</p>
      </div>

      {/* KPIs Row */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="animate-in fade-in slide-in-from-left duration-500">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Ingresos Totales</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">$8,420</div>
            <p className="text-xs text-gray-600">
              <span className="text-green-600 font-semibold">+12%</span> vs semana anterior
            </p>
          </CardContent>
        </Card>

        <Card className="animate-in fade-in slide-in-from-left duration-500" style={{ animationDelay: '100ms' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tickets Generados</CardTitle>
            <Zap className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">1,247</div>
            <p className="text-xs text-gray-600">
              +89 esta semana
            </p>
          </CardContent>
        </Card>

        <Card className="animate-in fade-in slide-in-from-left duration-500" style={{ animationDelay: '200ms' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Sesiones Activas</CardTitle>
            <Activity className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-purple-600">342</div>
            <p className="text-xs text-gray-600">
              En los últimos 30 minutos
            </p>
          </CardContent>
        </Card>

        <Card className="animate-in fade-in slide-in-from-left duration-500" style={{ animationDelay: '300ms' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Nodos Online</CardTitle>
            <Badge className="bg-emerald-100 text-emerald-800">14/17</Badge>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-emerald-600">82%</div>
            <p className="text-xs text-gray-600">
              Disponibilidad
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Tickets por día */}
        <Card className="animate-in fade-in slide-in-from-bottom duration-500 shadow-lg hover:shadow-xl transition-shadow">
          <CardHeader>
            <CardTitle>Tickets Generados (7 días)</CardTitle>
            <CardDescription>Tendencia diaria de generación de tickets</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={analytics?.tickets_by_day || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6', r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Ingresos por día */}
        <Card className="animate-in fade-in slide-in-from-bottom duration-500 shadow-lg hover:shadow-xl transition-shadow" style={{ animationDelay: '100ms' }}>
          <CardHeader>
            <CardTitle>Ingresos (7 días)</CardTitle>
            <CardDescription>Tendencia de ingresos diarios</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analytics?.revenue_trend || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip formatter={(value) => `$${value}`} />
                <Bar dataKey="revenue" fill="#10b981" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Distribución por plan */}
        <Card>
          <CardHeader>
            <CardTitle>Sesiones por Plan</CardTitle>
            <CardDescription>Distribución actual</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={analytics?.sessions_by_plan || []}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ plan, count }) => `${plan}: ${count}`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {(analytics?.sessions_by_plan || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Estado de nodos */}
        <Card>
          <CardHeader>
            <CardTitle>Estado de Nodos</CardTitle>
            <CardDescription>Distribución actual</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {analytics?.nodes_status.map((item, index) => (
                <div key={item.status} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: COLORS[index % COLORS.length] }}
                    />
                    <span className="font-medium">{item.status}</span>
                  </div>
                  <span className="text-2xl font-bold">{item.count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default DashboardAnalytics;
