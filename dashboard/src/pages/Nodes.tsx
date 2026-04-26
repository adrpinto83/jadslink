import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import apiClient from '@/api/client';
import { useGeolocation } from '@/hooks/useGeolocation';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import NodeMap from '@/components/NodeMap';
import { toast } from 'sonner';
import {
  MapPin,
  Wifi,
  WifiOff,
  Search,
  RefreshCcw,
  AlertCircle,
  Activity,
  Plus,
  Edit,
  Trash2,
  MoreVertical,
  Eye,
  Settings,
  Key
} from 'lucide-react';

// Define the Node type based on the backend schema
interface Node {
  id: string;
  name: string;
  serial: string;
  status: string;
  api_key?: string;
  last_seen_at: string | null;
  location: {
    lat: number | null;
    lng: number | null;
    address: string | null;
  } | null;
  config?: {
    ssid?: string;
    channel?: number;
    max_clients?: number;
    bandwidth_default?: number;
  } | null;
  current_sessions?: number;
  total_bandwidth_mb?: number;
}

const Nodes: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'online' | 'offline'>('all');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [newNodeData, setNewNodeData] = useState({
    name: '',
    serial: '',
    config: {
      ssid: 'JADSlink',
      channel: 6,
      max_clients: 10,
      bandwidth_default: 2000,
      api_endpoint: 'https://api.jadslink.io',
      heartbeat_interval: 30,
      metrics_interval: 60,
      enable_metrics: true,
    }
  });
  const [geoLocation, setGeoLocation] = useState<any | null>(null);
  const [loadingGeo, setLoadingGeo] = useState(false);
  const queryClient = useQueryClient();
  const { data: userLocation } = useGeolocation();

  const { data: nodes, isLoading, error, refetch, isRefetching } = useQuery<Node[], Error>({
    queryKey: ['nodes'],
    queryFn: async () => {
      const response = await apiClient.get('/nodes');
      return response.data;
    },
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  });

  // Create node mutation
  const createNodeMutation = useMutation({
    mutationFn: async (data: { name: string; serial: string; config: any }) => {
      const response = await apiClient.post('/nodes', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nodes'] });
      setCreateDialogOpen(false);
      setNewNodeData({
        name: '',
        serial: '',
        config: {
          ssid: 'JADSlink',
          channel: 6,
          max_clients: 10,
          bandwidth_default: 2000,
          api_endpoint: 'https://api.jadslink.io',
          heartbeat_interval: 30,
          metrics_interval: 60,
          enable_metrics: true,
        }
      });
      toast.success('Nodo creado exitosamente');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Error al crear el nodo');
    },
  });

  // Update node mutation
  const updateNodeMutation = useMutation({
    mutationFn: async (data: { id: string; name: string }) => {
      const response = await apiClient.patch(`/nodes/${data.id}`, { name: data.name });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nodes'] });
      setEditDialogOpen(false);
      setSelectedNode(null);
      toast.success('Nodo actualizado exitosamente');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Error al actualizar el nodo');
    },
  });

  // Delete node mutation
  const deleteNodeMutation = useMutation({
    mutationFn: async (nodeId: string) => {
      await apiClient.delete(`/nodes/${nodeId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nodes'] });
      setDeleteDialogOpen(false);
      setSelectedNode(null);
      toast.success('Nodo eliminado exitosamente');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Error al eliminar el nodo');
    },
  });

  // Detect location mutation
  const detectLocationMutation = useMutation({
    mutationFn: async (nodeId: string) => {
      const response = await apiClient.post(`/nodes/${nodeId}/detect-location`);
      return response.data;
    },
    onSuccess: (updatedNode: any) => {
      queryClient.invalidateQueries({ queryKey: ['nodes'] });
      toast.success(`✓ Ubicación detectada: ${updatedNode.location?.address}`);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Error al detectar ubicación');
    },
  });

  const handleCreateNode = () => {
    if (!newNodeData.name || !newNodeData.serial) {
      toast.error('Por favor completa todos los campos');
      return;
    }
    createNodeMutation.mutate(newNodeData);
  };

  const handleAutoLocation = async () => {
    setLoadingGeo(true);
    try {
      // Set name to location if empty
      if (!newNodeData.name && userLocation?.location) {
        setNewNodeData(prev => ({
          ...prev,
          name: `${userLocation.location.city}, ${userLocation.location.country}`
        }));
      }
      setGeoLocation(userLocation?.location);
      toast.success(`Ubicación detectada: ${userLocation?.location.address}`);
    } catch (error) {
      toast.error('No se pudo obtener la ubicación');
    } finally {
      setLoadingGeo(false);
    }
  };

  const handleUpdateNode = () => {
    if (!selectedNode || !selectedNode.name) {
      toast.error('Por favor completa todos los campos');
      return;
    }
    updateNodeMutation.mutate({ id: selectedNode.id, name: selectedNode.name });
  };

  const handleDeleteNode = () => {
    if (!selectedNode) return;
    deleteNodeMutation.mutate(selectedNode.id);
  };

  const handleDetectLocation = (nodeId: string) => {
    if (detectLocationMutation.isPending) return;
    detectLocationMutation.mutate(nodeId);
  };

  const copyApiKey = (apiKey: string) => {
    navigator.clipboard.writeText(apiKey);
    toast.success('API Key copiada al portapapeles');
  };

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
        <div className="flex gap-2">
          <Button
            onClick={() => refetch()}
            variant="outline"
            size="sm"
            disabled={isRefetching}
          >
            <RefreshCcw className={`h-4 w-4 mr-2 ${isRefetching ? 'animate-spin' : ''}`} />
            Actualizar
          </Button>
          <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button size="sm">
                <Plus className="h-4 w-4 mr-2" />
                Agregar Nodo
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Crear Nuevo Nodo</DialogTitle>
                <DialogDescription>
                  Agrega un nuevo punto de acceso a tu red
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="name">Nombre</Label>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={handleAutoLocation}
                      disabled={loadingGeo}
                      className="text-xs"
                    >
                      <MapPin className="h-3 w-3 mr-1" />
                      {loadingGeo ? 'Detectando...' : 'Auto-ubicación'}
                    </Button>
                  </div>
                  <Input
                    id="name"
                    placeholder="Ej: Bus 101, Playa La Guaira"
                    value={newNodeData.name}
                    onChange={(e) => setNewNodeData({ ...newNodeData, name: e.target.value })}
                  />
                  {geoLocation && (
                    <p className="text-xs text-gray-500">
                      📍 {geoLocation.address}
                    </p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="serial">Serial</Label>
                  <Input
                    id="serial"
                    placeholder="Ej: SN-ABC-001"
                    value={newNodeData.serial}
                    onChange={(e) => setNewNodeData({ ...newNodeData, serial: e.target.value })}
                  />
                </div>

                {/* WiFi Configuration Section */}
                <div className="border-t pt-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Wifi className="h-4 w-4 text-blue-600" />
                    <h4 className="font-semibold text-sm">Configuración WiFi</h4>
                  </div>

                  <div className="space-y-3">
                    <div className="space-y-2">
                      <Label htmlFor="ssid">SSID (Nombre de Red)</Label>
                      <Input
                        id="ssid"
                        placeholder="JADSlink"
                        value={newNodeData.config?.ssid || 'JADSlink'}
                        onChange={(e) =>
                          setNewNodeData({
                            ...newNodeData,
                            config: { ...newNodeData.config, ssid: e.target.value }
                          })
                        }
                      />
                      <p className="text-xs text-muted-foreground">
                        Nombre de la red WiFi visible a los usuarios
                      </p>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-2">
                        <Label htmlFor="channel">Canal WiFi</Label>
                        <Input
                          id="channel"
                          type="number"
                          min="1"
                          max="13"
                          value={newNodeData.config?.channel || 6}
                          onChange={(e) =>
                            setNewNodeData({
                              ...newNodeData,
                              config: {
                                ...newNodeData.config,
                                channel: parseInt(e.target.value) || 6
                              }
                            })
                          }
                        />
                        <p className="text-xs text-muted-foreground">
                          1-13
                        </p>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="max-clients">Máx. Clientes</Label>
                        <Input
                          id="max-clients"
                          type="number"
                          min="1"
                          value={newNodeData.config?.max_clients || 10}
                          onChange={(e) =>
                            setNewNodeData({
                              ...newNodeData,
                              config: {
                                ...newNodeData.config,
                                max_clients: parseInt(e.target.value) || 10
                              }
                            })
                          }
                        />
                        <p className="text-xs text-muted-foreground">
                          Conexiones simultáneas
                        </p>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="bandwidth">Ancho de Banda Predeterminado (Kbps)</Label>
                      <Input
                        id="bandwidth"
                        type="number"
                        min="256"
                        step="256"
                        value={newNodeData.config?.bandwidth_default || 2000}
                        onChange={(e) =>
                          setNewNodeData({
                            ...newNodeData,
                            config: {
                              ...newNodeData.config,
                              bandwidth_default: parseInt(e.target.value) || 2000
                            }
                          })
                        }
                      />
                      <p className="text-xs text-muted-foreground">
                        Velocidad asignada por defecto a cada usuario
                      </p>
                    </div>
                  </div>
                </div>

                {/* Router Communication Section */}
                <div className="border-t pt-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Activity className="h-4 w-4 text-green-600" />
                    <h4 className="font-semibold text-sm">Comunicación del Router</h4>
                  </div>

                  <div className="space-y-3">
                    <div className="space-y-2">
                      <Label htmlFor="api-endpoint">API Endpoint</Label>
                      <Input
                        id="api-endpoint"
                        placeholder="https://api.jadslink.io"
                        value={newNodeData.config?.api_endpoint || 'https://api.jadslink.io'}
                        onChange={(e) =>
                          setNewNodeData({
                            ...newNodeData,
                            config: {
                              ...newNodeData.config,
                              api_endpoint: e.target.value
                            }
                          })
                        }
                      />
                      <p className="text-xs text-muted-foreground">
                        URL del servidor backend para sincronización
                      </p>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-2">
                        <Label htmlFor="heartbeat">Intervalo Heartbeat (seg)</Label>
                        <Input
                          id="heartbeat"
                          type="number"
                          min="10"
                          max="300"
                          value={newNodeData.config?.heartbeat_interval || 30}
                          onChange={(e) =>
                            setNewNodeData({
                              ...newNodeData,
                              config: {
                                ...newNodeData.config,
                                heartbeat_interval: parseInt(e.target.value) || 30
                              }
                            })
                          }
                        />
                        <p className="text-xs text-muted-foreground">
                          Frecuencia de latidos (10-300)
                        </p>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="metrics">Intervalo Métricas (seg)</Label>
                        <Input
                          id="metrics"
                          type="number"
                          min="30"
                          max="600"
                          value={newNodeData.config?.metrics_interval || 60}
                          onChange={(e) =>
                            setNewNodeData({
                              ...newNodeData,
                              config: {
                                ...newNodeData.config,
                                metrics_interval: parseInt(e.target.value) || 60
                              }
                            })
                          }
                        />
                        <p className="text-xs text-muted-foreground">
                          Frecuencia de reportes (30-600)
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 p-2 bg-muted rounded">
                      <input
                        type="checkbox"
                        id="enable-metrics"
                        checked={newNodeData.config?.enable_metrics !== false}
                        onChange={(e) =>
                          setNewNodeData({
                            ...newNodeData,
                            config: {
                              ...newNodeData.config,
                              enable_metrics: e.target.checked
                            }
                          })
                        }
                        className="rounded"
                      />
                      <label htmlFor="enable-metrics" className="text-sm cursor-pointer flex-1">
                        Reportar métricas al servidor
                      </label>
                    </div>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setCreateDialogOpen(false)}
                  disabled={createNodeMutation.isPending}
                >
                  Cancelar
                </Button>
                <Button
                  onClick={handleCreateNode}
                  disabled={createNodeMutation.isPending}
                >
                  {createNodeMutation.isPending ? 'Creando...' : 'Crear Nodo'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
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
      <Card className="relative z-0">
        <CardHeader>
          <CardTitle>Mapa de Nodos</CardTitle>
          <CardDescription>
            Ubicación geográfica de todos los puntos de acceso
          </CardDescription>
        </CardHeader>
        <CardContent className="h-96 p-0 relative z-0">
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
              {!searchTerm && statusFilter === 'all' && (
                <Button
                  onClick={() => setCreateDialogOpen(true)}
                  className="mt-4"
                  size="sm"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Crear Primer Nodo
                </Button>
              )}
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
                    <TableHead>Sesiones</TableHead>
                    <TableHead>Última vez visto</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
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
                        {node.current_sessions !== undefined ? (
                          <Badge variant="outline">{node.current_sessions} activas</Badge>
                        ) : (
                          <span className="text-muted-foreground text-sm">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {node.last_seen_at ? (
                          <span className="text-sm">
                            {new Date(node.last_seen_at).toLocaleString('es-VE', {
                              dateStyle: 'short',
                              timeStyle: 'short'
                            })}
                          </span>
                        ) : (
                          <span className="text-muted-foreground text-sm">Nunca</span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button asChild variant="ghost" size="sm">
                            <Link to={`/dashboard/nodes/${node.id}`}>
                              <Eye className="h-4 w-4" />
                            </Link>
                          </Button>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm">
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuLabel>Acciones</DropdownMenuLabel>
                              <DropdownMenuItem
                                onClick={() => {
                                  setSelectedNode(node);
                                  setEditDialogOpen(true);
                                }}
                              >
                                <Edit className="h-4 w-4 mr-2" />
                                Editar
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={() => handleDetectLocation(node.id)}
                                disabled={detectLocationMutation.isPending}
                              >
                                <MapPin className="h-4 w-4 mr-2" />
                                {detectLocationMutation.isPending ? 'Detectando...' : 'Detectar Ubicación'}
                              </DropdownMenuItem>
                              {node.api_key && (
                                <DropdownMenuItem onClick={() => copyApiKey(node.api_key!)}>
                                  <Key className="h-4 w-4 mr-2" />
                                  Copiar API Key
                                </DropdownMenuItem>
                              )}
                              <DropdownMenuItem asChild>
                                <Link to={`/dashboard/nodes/${node.id}`}>
                                  <Settings className="h-4 w-4 mr-2" />
                                  Configurar
                                </Link>
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                className="text-destructive"
                                onClick={() => {
                                  setSelectedNode(node);
                                  setDeleteDialogOpen(true);
                                }}
                              >
                                <Trash2 className="h-4 w-4 mr-2" />
                                Eliminar
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Editar Nodo</DialogTitle>
            <DialogDescription>
              Modifica la información del nodo
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-name">Nombre</Label>
              <Input
                id="edit-name"
                value={selectedNode?.name || ''}
                onChange={(e) => setSelectedNode(selectedNode ? { ...selectedNode, name: e.target.value } : null)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-serial">Serial</Label>
              <Input
                id="edit-serial"
                value={selectedNode?.serial || ''}
                disabled
                className="bg-muted"
              />
              <p className="text-xs text-muted-foreground">El serial no puede modificarse</p>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setEditDialogOpen(false);
                setSelectedNode(null);
              }}
              disabled={updateNodeMutation.isPending}
            >
              Cancelar
            </Button>
            <Button
              onClick={handleUpdateNode}
              disabled={updateNodeMutation.isPending}
            >
              {updateNodeMutation.isPending ? 'Guardando...' : 'Guardar Cambios'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Estás seguro?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta acción no se puede deshacer. Esto eliminará permanentemente el nodo
              <strong className="block mt-2">{selectedNode?.name}</strong>
              y todos sus datos asociados.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel
              onClick={() => {
                setDeleteDialogOpen(false);
                setSelectedNode(null);
              }}
              disabled={deleteNodeMutation.isPending}
            >
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteNode}
              disabled={deleteNodeMutation.isPending}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleteNodeMutation.isPending ? 'Eliminando...' : 'Eliminar'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default Nodes;
