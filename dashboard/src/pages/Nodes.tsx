import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import apiClient from '@/api/client';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import NodeMap from '@/components/NodeMap';
import {
  MapPin,
  Wifi,
  WifiOff,
  Search,
  RefreshCcw,
  AlertCircle,
  Activity
} from 'lucide-react';

// Define the Node type based on the backend schema
interface Node {
  id: string;
  name: string;
  serial: string;
  status: string;
  last_seen_at: string | null;
  location: {
    lat: number | null;
    lng: number | null;
    address: string | null;
  } | null;
}

const Nodes: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'online' | 'offline'>('all');

  const { data: nodes, isLoading, error, refetch, isRefetching } = useQuery<Node[], Error>({
    queryKey: ['nodes'],
    queryFn: async () => {
      const response = await apiClient.get('/nodes');
      return response.data;
    },
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  });

  const getStatusVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (status.toLowerCase()) {
      case 'online':
        return 'default';
      case 'offline':
        return 'destructive';
      default:
        return 'secondary';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'online':
        return <Wifi className="h-4 w-4" />;
      case 'offline':
        return <WifiOff className="h-4 w-4" />;
      default:
        return <AlertCircle className="h-4 w-4" />;
    }
  };

  // Calculate stats
  const onlineNodes = nodes?.filter(n => n.status.toLowerCase() === 'online').length || 0;
  const offlineNodes = nodes?.filter(n => n.status.toLowerCase() === 'offline').length || 0;
  const totalNodes = nodes?.length || 0;
  const uptimePercentage = totalNodes > 0 ? Math.round((onlineNodes / totalNodes) * 100) : 0;

  // Filter nodes
  const filteredNodes = nodes?.filter(node => {
    const matchesSearch =
      node.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      node.serial.toLowerCase().includes(searchTerm.toLowerCase()) ||
      node.location?.address?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus =
      statusFilter === 'all' ||
      node.status.toLowerCase() === statusFilter;

    return matchesSearch && matchesStatus;
  }) || [];

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

  if (error) {
    return (
      <div className="space-y-6">
        <h2 className="text-3xl font-bold">Nodos</h2>
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <div className="text-center">
              <AlertCircle className="mx-auto h-12 w-12 text-destructive" />
              <p className="mt-2 text-lg font-medium">Error al cargar nodos</p>
              <p className="text-sm text-muted-foreground">{error.message}</p>
              <Button onClick={() => refetch()} className="mt-4">
                Reintentar
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Nodos</h2>
          <p className="text-muted-foreground">
            Gestiona y monitorea tus puntos de acceso
          </p>
        </div>
        <Button
          onClick={() => refetch()}
          variant="outline"
          size="sm"
          disabled={isRefetching}
        >
          <RefreshCcw className={`h-4 w-4 mr-2 ${isRefetching ? 'animate-spin' : ''}`} />
          Actualizar
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-4">
        <StatCard
          title="Total de Nodos"
          value={totalNodes}
          description="Puntos de acceso registrados"
          icon={MapPin}
          loading={isLoading}
        />
        <StatCard
          title="Nodos Online"
          value={onlineNodes}
          description="Activos y funcionando"
          icon={Wifi}
          loading={isLoading}
        />
        <StatCard
          title="Nodos Offline"
          value={offlineNodes}
          description="Desconectados o inactivos"
          icon={WifiOff}
          loading={isLoading}
        />
        <StatCard
          title="Disponibilidad"
          value={`${uptimePercentage}%`}
          description="Porcentaje de nodos online"
          icon={Activity}
          loading={isLoading}
        />
      </div>

      {/* Map */}
      <Card>
        <CardHeader>
          <CardTitle>Mapa de Nodos</CardTitle>
          <CardDescription>
            Ubicación geográfica de todos los puntos de acceso
          </CardDescription>
        </CardHeader>
        <CardContent className="h-96 p-0">
          {nodes && nodes.length > 0 ? (
            <NodeMap nodes={nodes} />
          ) : (
            <div className="h-full flex items-center justify-center">
              <p className="text-muted-foreground">No hay nodos con ubicación para mostrar</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Filters and Search */}
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
                  placeholder="Buscar por nombre, serial o ubicación..."
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
                Todos
              </Button>
              <Button
                variant={statusFilter === 'online' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setStatusFilter('online')}
              >
                Online
              </Button>
              <Button
                variant={statusFilter === 'offline' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setStatusFilter('offline')}
              >
                Offline
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Nodes Table */}
      <Card>
        <CardHeader>
          <CardTitle>Lista de Nodos</CardTitle>
          <CardDescription>
            {filteredNodes.length} nodo(s) encontrado(s)
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]" />
              <p className="mt-2 text-muted-foreground">Cargando nodos...</p>
            </div>
          ) : filteredNodes.length === 0 ? (
            <div className="text-center py-8">
              <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground" />
              <p className="mt-2 text-muted-foreground">
                {searchTerm || statusFilter !== 'all'
                  ? 'No se encontraron nodos con los filtros aplicados'
                  : 'No hay nodos registrados'}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Nombre</TableHead>
                    <TableHead>Serial</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead>Ubicación</TableHead>
                    <TableHead>Última vez visto</TableHead>
                    <TableHead>Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredNodes.map((node) => (
                    <TableRow key={node.id}>
                      <TableCell className="font-medium">{node.name}</TableCell>
                      <TableCell className="font-mono text-sm">{node.serial}</TableCell>
                      <TableCell>
                        <Badge
                          variant={getStatusVariant(node.status)}
                          className="flex items-center gap-1 w-fit"
                        >
                          {getStatusIcon(node.status)}
                          {node.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {node.location?.address ? (
                          <div className="flex items-center gap-1">
                            <MapPin className="h-3 w-3 text-muted-foreground" />
                            <span className="text-sm">{node.location.address}</span>
                          </div>
                        ) : (
                          <span className="text-muted-foreground text-sm">Sin ubicación</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {node.last_seen_at ? (
                          <span className="text-sm">
                            {new Date(node.last_seen_at).toLocaleString()}
                          </span>
                        ) : (
                          <span className="text-muted-foreground text-sm">Nunca</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Button asChild variant="outline" size="sm">
                          <Link to={`/dashboard/nodes/${node.id}`}>
                            Ver Detalles
                          </Link>
                        </Button>
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

export default Nodes;
