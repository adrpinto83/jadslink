import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
  Users,
  Server,
  Ticket,
  Activity,
  MapPin,
  Wifi,
  MoreVertical,
  AlertCircle,
} from 'lucide-react';
import {
  GlobalStats,
  TenantDetail,
  TenantStats,
  NodeAdmin,
  TicketAdmin,
  SessionAdmin,
  TicketsListResponse,
} from '@/types/admin';
import { Skeleton } from '@/components/ui/skeleton';

// ============================================================================
// COMPONENTES AUXILIARES
// ============================================================================

/**
 * Tarjeta de estadística con icono y descripción
 */
const StatCard = ({
  title,
  value,
  description,
  icon: Icon,
  variant = 'default',
}: {
  title: string;
  value: string | number;
  description?: string;
  icon?: React.ComponentType<{ className?: string }>;
  variant?: 'default' | 'success' | 'warning' | 'destructive';
}) => {
  const bgColor = {
    default: 'bg-blue-50 dark:bg-blue-950',
    success: 'bg-green-50 dark:bg-green-950',
    warning: 'bg-yellow-50 dark:bg-yellow-950',
    destructive: 'bg-red-50 dark:bg-red-950',
  }[variant];

  const iconColor = {
    default: 'text-blue-600 dark:text-blue-400',
    success: 'text-green-600 dark:text-green-400',
    warning: 'text-yellow-600 dark:text-yellow-400',
    destructive: 'text-red-600 dark:text-red-400',
  }[variant];

  return (
    <Card>
      <CardHeader className={`pb-2 ${bgColor}`}>
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {title}
          </CardTitle>
          {Icon && <Icon className={`h-4 w-4 ${iconColor}`} />}
        </div>
      </CardHeader>
      <CardContent className="pt-4">
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
      </CardContent>
    </Card>
  );
};

/**
 * Tabla de Nodos
 */
const NodesTable = ({ nodes, isLoading }: { nodes: NodeAdmin[] | undefined; isLoading: boolean }) => {
  if (isLoading) {
    return (
      <div className="space-y-2">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (!nodes || nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-muted-foreground">
        <AlertCircle className="h-4 w-4 mr-2" />
        No hay nodos disponibles
      </div>
    );
  }

  return (
    <div className="rounded-md border overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/50">
            <TableHead className="font-semibold">Nombre</TableHead>
            <TableHead className="font-semibold">Serial</TableHead>
            <TableHead className="font-semibold">Estado</TableHead>
            <TableHead className="font-semibold">Última vez visto</TableHead>
            <TableHead className="font-semibold">Ubicación</TableHead>
            <TableHead className="font-semibold text-right">IP WAN</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {nodes.map((node) => (
            <TableRow key={node.id} className="hover:bg-muted/50">
              <TableCell className="font-medium">{node.name}</TableCell>
              <TableCell className="font-mono text-sm">{node.serial}</TableCell>
              <TableCell>
                <Badge
                  variant={
                    node.status === 'online'
                      ? 'default'
                      : node.status === 'offline'
                        ? 'destructive'
                        : 'secondary'
                  }
                >
                  {node.status === 'online' && <Wifi className="h-3 w-3 mr-1" />}
                  {node.status}
                </Badge>
              </TableCell>
              <TableCell className="text-sm">
                {node.last_seen_at
                  ? new Date(node.last_seen_at).toLocaleString('es-VE')
                  : 'Nunca'}
              </TableCell>
              <TableCell className="text-sm">
                {node.location?.address ? (
                  <div className="flex items-start gap-1">
                    <MapPin className="h-4 w-4 mt-0.5 flex-shrink-0 text-gray-500" />
                    <span>{node.location.address}</span>
                  </div>
                ) : (
                  'N/A'
                )}
              </TableCell>
              <TableCell className="text-right text-sm font-mono">
                {node.wan_ip || 'N/A'}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};

/**
 * Tabla de Tickets
 */
const TicketsTable = ({
  data,
  isLoading,
  onPageChange,
}: {
  data: TicketsListResponse | undefined;
  isLoading: boolean;
  onPageChange: (page: number) => void;
}) => {
  const [currentPage, setCurrentPage] = useState(1);

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (!data || data.tickets.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-muted-foreground">
        <AlertCircle className="h-4 w-4 mr-2" />
        No hay tickets disponibles
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-md border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/50">
              <TableHead className="font-semibold">Código</TableHead>
              <TableHead className="font-semibold">Estado</TableHead>
              <TableHead className="font-semibold">Plan</TableHead>
              <TableHead className="font-semibold">Nodo</TableHead>
              <TableHead className="font-semibold">Creado</TableHead>
              <TableHead className="font-semibold">Activado</TableHead>
              <TableHead className="font-semibold">Expira</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.tickets.map((ticket) => (
              <TableRow key={ticket.id} className="hover:bg-muted/50">
                <TableCell className="font-mono font-semibold">{ticket.code}</TableCell>
                <TableCell>
                  <Badge
                    variant={
                      ticket.status === 'active'
                        ? 'default'
                        : ticket.status === 'expired'
                          ? 'secondary'
                          : ticket.status === 'revoked'
                            ? 'destructive'
                            : 'outline'
                    }
                  >
                    {ticket.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-sm">{ticket.plan_name || 'N/A'}</TableCell>
                <TableCell className="text-sm">{ticket.node_name || 'N/A'}</TableCell>
                <TableCell className="text-sm">
                  {new Date(ticket.created_at).toLocaleString('es-VE', {
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </TableCell>
                <TableCell className="text-sm">
                  {ticket.activated_at
                    ? new Date(ticket.activated_at).toLocaleString('es-VE', {
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                      })
                    : '-'}
                </TableCell>
                <TableCell className="text-sm">
                  {ticket.expires_at
                    ? new Date(ticket.expires_at).toLocaleString('es-VE', {
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                      })
                    : '-'}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Paginación */}
      {data.pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Página {data.page} de {data.pages} ({data.total} total)
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                if (currentPage > 1) {
                  setCurrentPage(currentPage - 1);
                  onPageChange(currentPage - 1);
                }
              }}
              disabled={currentPage === 1}
            >
              Anterior
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                if (currentPage < data.pages) {
                  setCurrentPage(currentPage + 1);
                  onPageChange(currentPage + 1);
                }
              }}
              disabled={currentPage === data.pages}
            >
              Siguiente
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Tabla de Sesiones
 */
const SessionsTable = ({ sessions, isLoading }: { sessions: SessionAdmin[] | undefined; isLoading: boolean }) => {
  if (isLoading) {
    return (
      <div className="space-y-2">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (!sessions || sessions.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-muted-foreground">
        <AlertCircle className="h-4 w-4 mr-2" />
        No hay sesiones disponibles
      </div>
    );
  }

  // Convertir bytes a formato legible
  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="rounded-md border overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/50">
            <TableHead className="font-semibold">MAC Dispositivo</TableHead>
            <TableHead className="font-semibold">IP</TableHead>
            <TableHead className="font-semibold">Nodo</TableHead>
            <TableHead className="font-semibold">Iniciado</TableHead>
            <TableHead className="font-semibold">Expira</TableHead>
            <TableHead className="font-semibold">Estado</TableHead>
            <TableHead className="font-semibold text-right">Bajada</TableHead>
            <TableHead className="font-semibold text-right">Subida</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sessions.map((session) => (
            <TableRow key={session.id} className="hover:bg-muted/50">
              <TableCell className="font-mono text-sm">{session.device_mac}</TableCell>
              <TableCell className="font-mono text-sm">{session.ip_address || 'N/A'}</TableCell>
              <TableCell className="text-sm">{session.node_name || 'N/A'}</TableCell>
              <TableCell className="text-sm">
                {new Date(session.started_at).toLocaleString('es-VE', {
                  month: '2-digit',
                  day: '2-digit',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </TableCell>
              <TableCell className="text-sm">
                {new Date(session.expires_at).toLocaleString('es-VE', {
                  month: '2-digit',
                  day: '2-digit',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </TableCell>
              <TableCell>
                <Badge variant={session.is_active ? 'default' : 'secondary'}>
                  {session.is_active ? 'Activa' : 'Expirada'}
                </Badge>
              </TableCell>
              <TableCell className="text-right text-sm">
                {formatBytes(session.bytes_down)}
              </TableCell>
              <TableCell className="text-right text-sm">
                {formatBytes(session.bytes_up)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};

// ============================================================================
// COMPONENTE PRINCIPAL
// ============================================================================

/**
 * Página de Gestión de Tenants para Superadmin
 * Permite ver estadísticas globales y recursos de cada tenant específico
 */
export default function AdminTenants() {
  const [selectedTenantId, setSelectedTenantId] = useState<string | null>(null);
  const [ticketsPage, setTicketsPage] = useState(0);

  // ========== QUERIES ==========

  // Query: Estadísticas globales
  const { data: globalStats, isLoading: globalStatsLoading } = useQuery<GlobalStats>({
    queryKey: ['admin', 'overview'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/overview');
      return response.data;
    },
    staleTime: 30000, // 30 segundos
  });

  // Query: Lista de todos los tenants
  const { data: tenants, isLoading: tenantsLoading } = useQuery<TenantDetail[]>({
    queryKey: ['admin', 'tenants'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/tenants');
      return response.data;
    },
    staleTime: 60000, // 1 minuto
  });

  // Query: Estadísticas del tenant seleccionado
  const { data: tenantStats, isLoading: tenantStatsLoading } = useQuery<TenantStats>({
    queryKey: ['admin', 'tenant-stats', selectedTenantId],
    queryFn: async () => {
      const response = await apiClient.get(`/admin/tenants/${selectedTenantId}/stats`);
      return response.data;
    },
    enabled: !!selectedTenantId,
    staleTime: 30000,
  });

  // Query: Nodos del tenant seleccionado
  const { data: nodes, isLoading: nodesLoading } = useQuery<NodeAdmin[]>({
    queryKey: ['admin', 'tenant-nodes', selectedTenantId],
    queryFn: async () => {
      const response = await apiClient.get(`/admin/tenants/${selectedTenantId}/nodes`);
      return response.data;
    },
    enabled: !!selectedTenantId,
    staleTime: 30000,
  });

  // Query: Tickets del tenant seleccionado
  const { data: ticketsData, isLoading: ticketsLoading } = useQuery<TicketsListResponse>({
    queryKey: ['admin', 'tenant-tickets', selectedTenantId, ticketsPage],
    queryFn: async () => {
      const skip = ticketsPage * 100;
      const response = await apiClient.get(
        `/admin/tenants/${selectedTenantId}/tickets?skip=${skip}&limit=100`
      );
      return response.data;
    },
    enabled: !!selectedTenantId,
    staleTime: 30000,
  });

  // Query: Sesiones del tenant seleccionado
  const { data: sessions, isLoading: sessionsLoading } = useQuery<SessionAdmin[]>({
    queryKey: ['admin', 'tenant-sessions', selectedTenantId],
    queryFn: async () => {
      const response = await apiClient.get(
        `/admin/tenants/${selectedTenantId}/sessions?active_only=false`
      );
      return response.data;
    },
    enabled: !!selectedTenantId,
    staleTime: 30000,
  });

  return (
    <div className="space-y-6 pb-10">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Gestión de Tenants</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Visualiza y gestiona todos los operadores y sus recursos en tiempo real
        </p>
      </div>

      {/* Stats Globales */}
      {globalStatsLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent className="pt-4">
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : globalStats ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Total Tenants"
            value={globalStats.total_tenants}
            description={`${globalStats.active_tenants} activos`}
            icon={Users}
            variant="default"
          />
          <StatCard
            title="Nodos Globales"
            value={globalStats.total_nodes}
            description={`${globalStats.online_nodes} online`}
            icon={Server}
            variant={globalStats.online_nodes > 0 ? 'success' : 'warning'}
          />
          <StatCard
            title="Tickets"
            value={globalStats.total_tickets}
            description={`${globalStats.active_tickets} activos`}
            icon={Ticket}
          />
          <StatCard
            title="Sesiones Activas"
            value={globalStats.active_sessions}
            icon={Activity}
            variant={globalStats.active_sessions > 0 ? 'success' : 'warning'}
          />
        </div>
      ) : null}

      {/* Selector de Tenant */}
      <Card>
        <CardHeader>
          <CardTitle>Seleccionar Operador</CardTitle>
          <CardDescription>
            Elige un tenant para ver sus nodos, tickets y sesiones
          </CardDescription>
        </CardHeader>
        <CardContent>
          {tenantsLoading ? (
            <Skeleton className="h-10 w-full" />
          ) : (
            <Select value={selectedTenantId || ''} onValueChange={setSelectedTenantId}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Selecciona un tenant..." />
              </SelectTrigger>
              <SelectContent>
                {tenants?.map((tenant) => (
                  <SelectItem key={tenant.id} value={tenant.id}>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{tenant.name}</span>
                      <Badge variant="outline" className="text-xs">
                        {tenant.plan_tier}
                      </Badge>
                      {!tenant.is_active && (
                        <Badge variant="destructive" className="text-xs">
                          Inactivo
                        </Badge>
                      )}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </CardContent>
      </Card>

      {/* Stats del Tenant Seleccionado */}
      {selectedTenantId && tenantStats && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          <StatCard
            title="Nodos"
            value={tenantStats.nodes_total}
            description={`${tenantStats.nodes_online} online`}
            icon={Server}
            variant={tenantStats.nodes_online > 0 ? 'success' : 'warning'}
          />
          <StatCard
            title="Tickets"
            value={tenantStats.tickets_total}
            description={`${tenantStats.tickets_active} activos`}
            icon={Ticket}
          />
          <StatCard
            title="Sesiones"
            value={tenantStats.sessions_active}
            icon={Activity}
            variant={tenantStats.sessions_active > 0 ? 'success' : 'warning'}
          />
          <StatCard
            title="Ingresos"
            value={`$${tenantStats.revenue_estimate.toFixed(2)}`}
            description="Estimado"
          />
          <StatCard
            title="Estado"
            value={tenantStats.is_active ? 'Activo' : 'Inactivo'}
            variant={tenantStats.is_active ? 'success' : 'destructive'}
          />
        </div>
      )}

      {/* Tabs: Recursos del Tenant */}
      {selectedTenantId && (
        <Card>
          <CardHeader>
            <CardTitle>Recursos del Operador</CardTitle>
            <CardDescription>
              Información detallada de nodos, tickets y sesiones
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="nodes" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="nodes">
                  Nodos ({tenantStats?.nodes_total || 0})
                </TabsTrigger>
                <TabsTrigger value="tickets">
                  Tickets ({tenantStats?.tickets_total || 0})
                </TabsTrigger>
                <TabsTrigger value="sessions">
                  Sesiones ({tenantStats?.sessions_active || 0})
                </TabsTrigger>
              </TabsList>

              {/* Tab: Nodos */}
              <TabsContent value="nodes" className="space-y-4 mt-4">
                <NodesTable nodes={nodes} isLoading={nodesLoading} />
              </TabsContent>

              {/* Tab: Tickets */}
              <TabsContent value="tickets" className="space-y-4 mt-4">
                <TicketsTable
                  data={ticketsData}
                  isLoading={ticketsLoading}
                  onPageChange={setTicketsPage}
                />
              </TabsContent>

              {/* Tab: Sesiones */}
              <TabsContent value="sessions" className="space-y-4 mt-4">
                <SessionsTable sessions={sessions} isLoading={sessionsLoading} />
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}

      {/* Mensaje cuando no hay tenant seleccionado */}
      {!selectedTenantId && (
        <Card className="border-dashed">
          <CardContent className="pt-6 text-center">
            <AlertCircle className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
            <p className="text-muted-foreground">
              Selecciona un operador en el dropdown superior para ver sus recursos
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
