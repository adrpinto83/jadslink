import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Users,
  Clock,
  Wifi,
  AlertCircle,
  Power,
  Search
} from 'lucide-react';

interface Session {
  id: string;
  ticket_code: string;
  mac_address: string;
  status: 'active' | 'ended' | 'expired';
  started_at: string;
  ended_at: string | null;
  duration_minutes: number;
  node: {
    id: string;
    name: string;
  } | null;
  plan: {
    id: string;
    name: string;
    duration_minutes: number;
  } | null;
}

const Sessions: React.FC = () => {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'ended' | 'expired'>('all');

  // Fetch all sessions with auto-refresh
  const { data: sessions, isLoading } = useQuery<Session[]>({
    queryKey: ['sessions'],
    queryFn: async () => {
      const response = await apiClient.get('/sessions');
      return response.data;
    },
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  // Mutation to disconnect a session
  const disconnectMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      await apiClient.post(`/sessions/${sessionId}/disconnect`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
    onError: (error: any) => {
      alert(`Error disconnecting session: ${error.message}`);
    }
  });

  // Calculate stats
  const activeSessions = sessions?.filter(s => s.status === 'active') || [];
  const totalSessions = sessions?.length || 0;

  // Calculate average duration for ended sessions
  const endedSessions = sessions?.filter(s => s.status === 'ended' && s.ended_at) || [];
  const avgDuration = endedSessions.length > 0
    ? endedSessions.reduce((sum, s) => {
        const start = new Date(s.started_at).getTime();
        const end = new Date(s.ended_at!).getTime();
        return sum + (end - start) / 1000 / 60; // minutes
      }, 0) / endedSessions.length
    : 0;

  // Filter sessions
  const filteredSessions = sessions?.filter(session => {
    const matchesSearch =
      session.ticket_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      session.mac_address.toLowerCase().includes(searchTerm.toLowerCase()) ||
      session.node?.name.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = statusFilter === 'all' || session.status === statusFilter;

    return matchesSearch && matchesStatus;
  }) || [];

  // Calculate time remaining for active session
  const getTimeRemaining = (session: Session): string => {
    if (session.status !== 'active' || !session.plan) return '-';

    const startTime = new Date(session.started_at).getTime();
    const now = Date.now();
    const elapsedMinutes = (now - startTime) / 1000 / 60;
    const remainingMinutes = session.plan.duration_minutes - elapsedMinutes;

    if (remainingMinutes <= 0) return 'Expired';

    const hours = Math.floor(remainingMinutes / 60);
    const minutes = Math.floor(remainingMinutes % 60);

    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  const getStatusVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (status) {
      case 'active':
        return 'default';
      case 'ended':
        return 'secondary';
      case 'expired':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  const handleDisconnect = (sessionId: string) => {
    if (window.confirm('¿Estás seguro de que quieres desconectar esta sesión?')) {
      disconnectMutation.mutate(sessionId);
    }
  };

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
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Sesiones</h2>
        <p className="text-muted-foreground">
          Gestiona las sesiones activas y el historial de conexiones
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-3">
        <StatCard
          title="Sesiones Activas"
          value={activeSessions.length}
          description="Usuarios conectados ahora"
          icon={Users}
          loading={isLoading}
        />
        <StatCard
          title="Total de Sesiones"
          value={totalSessions}
          description="Histórico completo"
          icon={Clock}
          loading={isLoading}
        />
        <StatCard
          title="Duración Promedio"
          value={`${Math.round(avgDuration)} min`}
          description="De sesiones finalizadas"
          icon={Wifi}
          loading={isLoading}
        />
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filtros</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Buscar por código, MAC o nodo..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                variant={statusFilter === 'all' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setStatusFilter('all')}
              >
                Todas
              </Button>
              <Button
                variant={statusFilter === 'active' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setStatusFilter('active')}
              >
                Activas
              </Button>
              <Button
                variant={statusFilter === 'ended' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setStatusFilter('ended')}
              >
                Finalizadas
              </Button>
              <Button
                variant={statusFilter === 'expired' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setStatusFilter('expired')}
              >
                Expiradas
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Sessions Table */}
      <Card>
        <CardHeader>
          <CardTitle>Lista de Sesiones</CardTitle>
          <CardDescription>
            {filteredSessions.length} sesion(es) encontrada(s)
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]" />
              <p className="mt-2 text-muted-foreground">Cargando sesiones...</p>
            </div>
          ) : filteredSessions.length === 0 ? (
            <div className="text-center py-8">
              <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground" />
              <p className="mt-2 text-muted-foreground">No se encontraron sesiones</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Código Ticket</TableHead>
                    <TableHead>Dirección MAC</TableHead>
                    <TableHead>Nodo</TableHead>
                    <TableHead>Plan</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead>Iniciada</TableHead>
                    <TableHead>Tiempo Restante</TableHead>
                    <TableHead>Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredSessions.map((session) => (
                    <TableRow key={session.id}>
                      <TableCell className="font-mono text-sm">
                        {session.ticket_code}
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {session.mac_address}
                      </TableCell>
                      <TableCell>
                        {session.node?.name || 'N/A'}
                      </TableCell>
                      <TableCell>
                        {session.plan?.name || 'N/A'}
                        {session.plan && (
                          <span className="text-xs text-muted-foreground ml-1">
                            ({session.plan.duration_minutes}min)
                          </span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusVariant(session.status)}>
                          {session.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {new Date(session.started_at).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <span className={
                          session.status === 'active' && getTimeRemaining(session) !== 'Expired'
                            ? 'text-green-600 dark:text-green-400 font-medium'
                            : 'text-muted-foreground'
                        }>
                          {getTimeRemaining(session)}
                        </span>
                      </TableCell>
                      <TableCell>
                        {session.status === 'active' && (
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => handleDisconnect(session.id)}
                            disabled={disconnectMutation.isPending}
                          >
                            <Power className="h-4 w-4 mr-1" />
                            Desconectar
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Sessions;
