import React, { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useReactToPrint } from 'react-to-print';
import {
  Ticket as TicketIcon,
  Search,
  Printer,
  AlertCircle,
  CheckCircle,
  Clock,
  XCircle
} from 'lucide-react';

// --- Type Definitions ---
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

interface Tenant {
  id: string;
  name: string;
  settings: {
    logo_url?: string;
  }
}

interface TicketData {
  id: string;
  code: string;
  status: 'pending' | 'active' | 'used' | 'expired';
  qr_data: string;
  qr_base64_png?: string;
  created_at: string;
  activated_at: string | null;
  node: {
    id: string;
    name: string;
  } | null;
  plan: {
    id: string;
    name: string;
    duration_minutes: number;
    price_usd: number;
  } | null;
}

interface GeneratedTicket {
  id: string;
  code: string;
  qr_data: string;
  qr_base64_png?: string;
}

// --- Printable Ticket Component ---
const PrintableTicket = React.forwardRef<HTMLDivElement, { ticket: GeneratedTicket | TicketData, tenant: Tenant | undefined }>(({ ticket, tenant }, ref) => (
  <div ref={ref} className="ticket-print p-6 border rounded-lg text-center space-y-4 bg-white">
    {tenant?.settings?.logo_url && (
      <img src={tenant.settings.logo_url} alt={`${tenant.name} Logo`} className="w-32 h-auto mx-auto" />
    )}
    <h3 className="text-xl font-bold text-gray-800">Ticket de Acceso</h3>
    <p className="text-gray-600">Usa este código QR para conectarte</p>
    {ticket.qr_base64_png && (
      <img
        src={ticket.qr_base64_png}
        alt={`QR Code for ${ticket.code}`}
        className="w-64 h-64 mx-auto"
      />
    )}
    <p className="font-mono text-4xl font-bold tracking-widest text-gray-900">{ticket.code}</p>
    <style type="text/css">
      {`
        @media print {
          body * {
            visibility: hidden;
          }
          .ticket-print, .ticket-print * {
            visibility: visible;
          }
          .ticket-print {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
          }
        }
      `}
    </style>
  </div>
));

const Tickets: React.FC = () => {
  const queryClient = useQueryClient();

  // --- State Management for Generation ---
  const [selectedNode, setSelectedNode] = useState<string>('');
  const [selectedPlan, setSelectedPlan] = useState<string>('');
  const [quantity, setQuantity] = useState<number>(1);
  const [generatedTickets, setGeneratedTickets] = useState<GeneratedTicket[]>([]);

  const ticketToPrintRef = useRef<HTMLDivElement>(null);
  const [selectedTicketForPrint, setSelectedTicketForPrint] = useState<GeneratedTicket | TicketData | null>(null);

  // --- State Management for Viewing All Tickets ---
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'pending' | 'active' | 'used' | 'expired'>('all');

  // --- Data Fetching ---
  const { data: nodes, isLoading: isLoadingNodes } = useQuery<Node[]>({
    queryKey: ['nodes'],
    queryFn: () => apiClient.get('/nodes').then(res => res.data)
  });

  const { data: plans, isLoading: isLoadingPlans } = useQuery<Plan[]>({
    queryKey: ['plans'],
    queryFn: () => apiClient.get('/plans').then(res => res.data)
  });

  const { data: tenant } = useQuery<Tenant>({
    queryKey: ['tenant'],
    queryFn: () => apiClient.get('/tenants/me').then(res => res.data)
  });

  const { data: allTickets, isLoading: isLoadingAllTickets } = useQuery<TicketData[]>({
    queryKey: ['all-tickets'],
    queryFn: () => apiClient.get('/tickets').then(res => res.data),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // --- Mutations ---
  const generateTicketsMutation = useMutation<GeneratedTicket[], Error, { node_id: string; plan_id: string; quantity: number }>({
    mutationFn: async (data) => {
      const response = await apiClient.post('/tickets/generate', data);
      return response.data;
    },
    onSuccess: (newTickets) => {
      setGeneratedTickets(newTickets);
      queryClient.invalidateQueries({ queryKey: ['all-tickets'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
    onError: (error) => {
      alert(`Error generating tickets: ${error.message}`);
    }
  });

  // --- Calculate Stats ---
  const pendingTickets = allTickets?.filter(t => t.status === 'pending').length || 0;
  const activeTickets = allTickets?.filter(t => t.status === 'active').length || 0;
  const usedTickets = allTickets?.filter(t => t.status === 'used').length || 0;
  const expiredTickets = allTickets?.filter(t => t.status === 'expired').length || 0;
  const totalRevenue = allTickets?.filter(t => t.status !== 'pending').reduce((sum, t) => sum + (t.plan?.price_usd || 0), 0) || 0;

  // --- Filter Tickets ---
  const filteredTickets = allTickets?.filter(ticket => {
    const matchesSearch =
      ticket.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ticket.node?.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ticket.plan?.name.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = statusFilter === 'all' || ticket.status === statusFilter;

    return matchesSearch && matchesStatus;
  }) || [];

  // --- Print Handler ---
  const handlePrint = useReactToPrint({
    contentRef: ticketToPrintRef,
  });

  const triggerPrint = (ticket: GeneratedTicket | TicketData) => {
    setSelectedTicketForPrint(ticket);
    setTimeout(handlePrint, 50);
  }

  // --- Event Handlers ---
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedNode || !selectedPlan || quantity < 1) {
      alert('Por favor selecciona un nodo, un plan y cantidad válida.');
      return;
    }
    generateTicketsMutation.mutate({ node_id: selectedNode, plan_id: selectedPlan, quantity });
  };

  const getStatusVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (status) {
      case 'active':
        return 'default';
      case 'pending':
        return 'outline';
      case 'used':
        return 'secondary';
      case 'expired':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-4 w-4" />;
      case 'pending':
        return <Clock className="h-4 w-4" />;
      case 'used':
        return <CheckCircle className="h-4 w-4" />;
      case 'expired':
        return <XCircle className="h-4 w-4" />;
      default:
        return <AlertCircle className="h-4 w-4" />;
    }
  };

  const isLoading = isLoadingNodes || isLoadingPlans;

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
        <h2 className="text-3xl font-bold tracking-tight">Tickets</h2>
        <p className="text-muted-foreground">
          Genera y gestiona tickets de acceso para tus usuarios
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <StatCard
          title="Pendientes"
          value={pendingTickets}
          description="Sin activar"
          icon={Clock}
          loading={isLoadingAllTickets}
        />
        <StatCard
          title="Activos"
          value={activeTickets}
          description="En uso ahora"
          icon={CheckCircle}
          loading={isLoadingAllTickets}
        />
        <StatCard
          title="Usados"
          value={usedTickets}
          description="Completados"
          icon={CheckCircle}
          loading={isLoadingAllTickets}
        />
        <StatCard
          title="Expirados"
          value={expiredTickets}
          description="Vencidos"
          icon={XCircle}
          loading={isLoadingAllTickets}
        />
        <StatCard
          title="Ingresos"
          value={`$${totalRevenue.toFixed(2)}`}
          description="De tickets vendidos"
          icon={TicketIcon}
          loading={isLoadingAllTickets}
        />
      </div>

      {/* Tabs for Generate vs View All */}
      <Tabs defaultValue="generate" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="generate">Generar Tickets</TabsTrigger>
          <TabsTrigger value="view">Ver Todos los Tickets</TabsTrigger>
        </TabsList>

        {/* Generate Tickets Tab */}
        <TabsContent value="generate" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Generar Nuevos Tickets</CardTitle>
              <CardDescription>Crea tickets de acceso para vender a tus clientes</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="node">Nodo</Label>
                    <select
                      id="node"
                      value={selectedNode}
                      onChange={(e) => setSelectedNode(e.target.value)}
                      className="w-full p-2 border rounded mt-1"
                      disabled={isLoading}
                    >
                      <option value="">{isLoading ? 'Cargando...' : 'Selecciona un Nodo'}</option>
                      {nodes?.map((node) => <option key={node.id} value={node.id}>{node.name}</option>)}
                    </select>
                  </div>
                  <div>
                    <Label htmlFor="plan">Plan</Label>
                    <select
                      id="plan"
                      value={selectedPlan}
                      onChange={(e) => setSelectedPlan(e.target.value)}
                      className="w-full p-2 border rounded mt-1"
                      disabled={isLoading}
                    >
                      <option value="">{isLoading ? 'Cargando...' : 'Selecciona un Plan'}</option>
                      {plans?.map((plan) => (
                        <option key={plan.id} value={plan.id}>
                          {plan.name} ({plan.duration_minutes} min - ${plan.price_usd})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <Label htmlFor="quantity">Cantidad</Label>
                    <Input
                      id="quantity"
                      type="number"
                      min="1"
                      max="50"
                      value={quantity}
                      onChange={(e) => setQuantity(parseInt(e.target.value))}
                      disabled={generateTicketsMutation.isPending}
                      className="mt-1"
                    />
                  </div>
                </div>
                <Button type="submit" disabled={generateTicketsMutation.isPending || isLoading}>
                  {generateTicketsMutation.isPending ? 'Generando...' : 'Generar Tickets'}
                </Button>
              </form>
            </CardContent>
          </Card>

          {generateTicketsMutation.isSuccess && generatedTickets.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Tickets Generados</CardTitle>
                <CardDescription>{generatedTickets.length} ticket(s) creado(s) exitosamente</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {generatedTickets.map((ticket) => (
                    <div key={ticket.id} className="p-4 border rounded-lg text-center space-y-2">
                      <p className="font-mono text-lg font-bold">{ticket.code}</p>
                      {ticket.qr_base64_png ? (
                        <img src={ticket.qr_base64_png} alt={`QR Code for ${ticket.code}`} className="w-48 h-48 mx-auto" />
                      ) : (
                        <div className="w-48 h-48 bg-gray-200 flex items-center justify-center mx-auto text-sm text-gray-500">No QR Image</div>
                      )}
                      <Button variant="outline" size="sm" onClick={() => triggerPrint(ticket)}>
                        <Printer className="h-4 w-4 mr-2" />
                        Imprimir
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* View All Tickets Tab */}
        <TabsContent value="view" className="space-y-6">
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
                      placeholder="Buscar por código, nodo o plan..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-8"
                    />
                  </div>
                </div>
                <div className="flex gap-2 flex-wrap">
                  <Button
                    variant={statusFilter === 'all' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setStatusFilter('all')}
                  >
                    Todos
                  </Button>
                  <Button
                    variant={statusFilter === 'pending' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setStatusFilter('pending')}
                  >
                    Pendientes
                  </Button>
                  <Button
                    variant={statusFilter === 'active' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setStatusFilter('active')}
                  >
                    Activos
                  </Button>
                  <Button
                    variant={statusFilter === 'used' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setStatusFilter('used')}
                  >
                    Usados
                  </Button>
                  <Button
                    variant={statusFilter === 'expired' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setStatusFilter('expired')}
                  >
                    Expirados
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Tickets Table */}
          <Card>
            <CardHeader>
              <CardTitle>Lista de Tickets</CardTitle>
              <CardDescription>
                {filteredTickets.length} ticket(s) encontrado(s)
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoadingAllTickets ? (
                <div className="text-center py-8">
                  <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]" />
                  <p className="mt-2 text-muted-foreground">Cargando tickets...</p>
                </div>
              ) : filteredTickets.length === 0 ? (
                <div className="text-center py-8">
                  <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground" />
                  <p className="mt-2 text-muted-foreground">No se encontraron tickets</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Código</TableHead>
                        <TableHead>Nodo</TableHead>
                        <TableHead>Plan</TableHead>
                        <TableHead>Estado</TableHead>
                        <TableHead>Creado</TableHead>
                        <TableHead>Activado</TableHead>
                        <TableHead>Acciones</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredTickets.map((ticket) => (
                        <TableRow key={ticket.id}>
                          <TableCell className="font-mono text-sm font-medium">
                            {ticket.code}
                          </TableCell>
                          <TableCell>
                            {ticket.node?.name || 'N/A'}
                          </TableCell>
                          <TableCell>
                            {ticket.plan?.name || 'N/A'}
                            {ticket.plan && (
                              <span className="text-xs text-muted-foreground ml-1">
                                ({ticket.plan.duration_minutes}min - ${ticket.plan.price_usd})
                              </span>
                            )}
                          </TableCell>
                          <TableCell>
                            <Badge variant={getStatusVariant(ticket.status)} className="flex items-center gap-1 w-fit">
                              {getStatusIcon(ticket.status)}
                              {ticket.status}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {new Date(ticket.created_at).toLocaleString()}
                          </TableCell>
                          <TableCell>
                            {ticket.activated_at ? new Date(ticket.activated_at).toLocaleString() : '-'}
                          </TableCell>
                          <TableCell>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => triggerPrint(ticket)}
                            >
                              <Printer className="h-4 w-4 mr-1" />
                              Imprimir
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
        </TabsContent>
      </Tabs>

      {/* Hidden component for printing */}
      <div style={{ display: "none" }}>
        {selectedTicketForPrint && <PrintableTicket ref={ticketToPrintRef} ticket={selectedTicketForPrint} tenant={tenant} />}
      </div>
    </div>
  );
};

export default Tickets;
