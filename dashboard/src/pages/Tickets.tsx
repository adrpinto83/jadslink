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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
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
import { useReactToPrint } from 'react-to-print';
import { toast } from 'sonner';
import {
  Search,
  Printer,
  AlertCircle,
  CheckCircle,
  Clock,
  XCircle,
  Share2,
  Copy,
  Eye,
  Ban,
  MoreVertical,
  Wifi,
  DollarSign
} from 'lucide-react';

// --- Type Definitions ---
interface Node {
  id: string;
  name: string;
  serial: string;
  location?: {
    lat: number | null;
    lng: number | null;
    address: string | null;
  };
  config?: {
    ssid?: string;
    channel?: number;
    max_clients?: number;
  };
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
  settings?: {
    logo_url?: string;
    primary_color?: string;
    ssid?: string;
    contact_email?: string;
    contact_phone?: string;
  };
}

interface TicketData {
  id: string;
  code: string;
  status: 'pending' | 'active' | 'used' | 'expired' | 'revoked';
  qr_data: string;
  qr_base64_png?: string;
  created_at: string;
  activated_at: string | null;
  expires_at: string | null;
  node: Node | null;
  plan: Plan | null;
}

interface GeneratedTicket {
  id: string;
  code: string;
  qr_data: string;
  qr_base64_png?: string;
  status: string;
  created_at: string;
}

// --- Compact Printable Ticket Component (3 per page) ---
const PrintableTicket = React.forwardRef<HTMLDivElement, {
  ticket: GeneratedTicket | TicketData;
  tenant: Tenant | undefined;
  node: Node | undefined;
  plan: Plan | undefined;
}>(({ ticket, tenant, node, plan }, ref) => {
  const ssid = tenant?.settings?.ssid || node?.config?.ssid || 'JADSlink WiFi';
  const logoUrl = tenant?.settings?.logo_url;
  const contactEmail = tenant?.settings?.contact_email;
  const contactPhone = tenant?.settings?.contact_phone;

  return (
    <div ref={ref} className="bg-white p-4 border-2 border-gray-300 rounded-lg" style={{ pageBreakInside: 'avoid' }}>
      {/* Compact Header */}
      <div className="flex items-center justify-between border-b-2 border-gray-200 pb-2 mb-3">
        <div className="flex items-center gap-2">
          {logoUrl ? (
            <img src={logoUrl} alt={tenant?.name} className="h-8 w-auto" />
          ) : (
            <Wifi className="h-6 w-6 text-blue-600" />
          )}
          <div>
            <h2 className="text-lg font-bold text-gray-800">{tenant?.name || 'JADSlink'}</h2>
            <p className="text-xs text-gray-600">Ticket WiFi</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {/* QR Code - Smaller */}
        <div className="flex flex-col items-center bg-gray-50 rounded p-2 border border-gray-300">
          {ticket.qr_base64_png ? (
            <img
              src={ticket.qr_base64_png}
              alt={`QR ${ticket.code}`}
              className="w-32 h-32 object-contain"
              style={{ imageRendering: 'pixelated' }}
            />
          ) : (
            <div className="w-32 h-32 bg-gray-200 flex items-center justify-center">
              <p className="text-xs text-gray-500">Sin QR</p>
            </div>
          )}
          <div className="mt-2 text-center w-full">
            <p className="text-xs text-gray-600">Código</p>
            <p className="font-mono text-xl font-bold tracking-wide text-gray-900 bg-white px-2 py-1 rounded border border-gray-300">
              {ticket.code}
            </p>
          </div>
        </div>

        {/* Details */}
        <div className="space-y-2">
          {/* WiFi SSID - Prominent */}
          <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded p-2">
            <div className="flex items-center gap-1 mb-1">
              <Wifi className="h-4 w-4" />
              <p className="text-xs font-semibold">Red WiFi</p>
            </div>
            <p className="text-lg font-bold">{ssid}</p>
          </div>

          {/* Plan Info */}
          {plan && (
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-blue-50 p-2 rounded">
                <p className="text-gray-600">Plan</p>
                <p className="font-semibold text-gray-800">{plan.name}</p>
              </div>
              <div className="bg-green-50 p-2 rounded">
                <p className="text-gray-600">Tiempo</p>
                <p className="font-semibold text-gray-800">{plan.duration_minutes}min</p>
              </div>
              <div className="bg-purple-50 p-2 rounded">
                <p className="text-gray-600">Precio</p>
                <p className="font-semibold text-gray-800">${plan.price_usd.toFixed(2)}</p>
              </div>
              {node && (
                <div className="bg-orange-50 p-2 rounded">
                  <p className="text-gray-600">Nodo</p>
                  <p className="font-semibold text-gray-800 truncate">{node.name}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Compact Instructions */}
      <div className="bg-yellow-50 border-l-2 border-yellow-400 p-2 mt-3">
        <p className="text-xs font-semibold text-yellow-800 mb-1">Pasos:</p>
        <ol className="text-xs text-yellow-700 list-decimal list-inside space-y-0.5">
          <li>Conéctate a WiFi: <strong>{ssid}</strong></li>
          <li>Abre tu navegador</li>
          <li>Escanea QR o ingresa código</li>
        </ol>
      </div>

      {/* Compact Footer */}
      <div className="border-t border-gray-200 pt-2 mt-2 text-center">
        {(contactEmail || contactPhone) && (
          <p className="text-xs text-gray-600">
            {contactEmail && <span>{contactEmail}</span>}
            {contactEmail && contactPhone && <span> • </span>}
            {contactPhone && <span>{contactPhone}</span>}
          </p>
        )}
      </div>
    </div>
  );
});
PrintableTicket.displayName = 'PrintableTicket';

const Tickets: React.FC = () => {
  const queryClient = useQueryClient();

  // --- State Management ---
  const [selectedNode, setSelectedNode] = useState<string>('');
  const [selectedPlan, setSelectedPlan] = useState<string>('');
  const [quantity, setQuantity] = useState<number>(1);
  const [generatedTickets, setGeneratedTickets] = useState<GeneratedTicket[]>([]);
  const [selectedTicketForPrint, setSelectedTicketForPrint] = useState<GeneratedTicket | TicketData | null>(null);
  const [selectedTicketForView, setSelectedTicketForView] = useState<TicketData | null>(null);
  const [ticketToRevoke, setTicketToRevoke] = useState<TicketData | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'pending' | 'active' | 'used' | 'expired' | 'revoked'>('all');
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [revokeDialogOpen, setRevokeDialogOpen] = useState(false);
  const [selectedTicketsForBatchPrint, setSelectedTicketsForBatchPrint] = useState<Set<string>>(new Set());
  const [ticketsToPrintBatch, setTicketsToPrintBatch] = useState<TicketData[]>([]);
  const [showQrInPrint, setShowQrInPrint] = useState(false);

  const ticketToPrintRef = useRef<HTMLDivElement>(null);
  const batchPrintRef = useRef<HTMLDivElement>(null);

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
    refetchInterval: 30000,
  });

  // --- Mutations ---
  const generateTicketsMutation = useMutation({
    mutationFn: async (data: { node_id: string; plan_id: string; quantity: number }) => {
      const response = await apiClient.post('/tickets/generate', data);
      return response.data;
    },
    onSuccess: (newTickets: GeneratedTicket[]) => {
      setGeneratedTickets(newTickets);
      queryClient.invalidateQueries({ queryKey: ['all-tickets'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
      toast.success(`${newTickets.length} ticket(s) generado(s) exitosamente`);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Error al generar tickets');
    }
  });

  const revokeTicketMutation = useMutation({
    mutationFn: async (ticketId: string) => {
      await apiClient.post(`/tickets/${ticketId}/revoke`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['all-tickets'] });
      setRevokeDialogOpen(false);
      setTicketToRevoke(null);
      toast.success('Ticket revocado exitosamente');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Error al revocar ticket');
    }
  });

  // --- Handlers ---
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedNode || !selectedPlan || quantity < 1) {
      toast.error('Por favor completa todos los campos');
      return;
    }
    generateTicketsMutation.mutate({ node_id: selectedNode, plan_id: selectedPlan, quantity });
  };

  const handlePrint = useReactToPrint({
    contentRef: ticketToPrintRef,
  });

  const handleBatchPrint = useReactToPrint({
    contentRef: batchPrintRef,
  });

  const triggerPrint = (ticket: GeneratedTicket | TicketData) => {
    setSelectedTicketForPrint(ticket);
    setTimeout(handlePrint, 100);
  };

  const triggerBatchPrint = () => {
    const ticketsToPrint = filteredTickets.filter(t => selectedTicketsForBatchPrint.has(t.id));
    if (ticketsToPrint.length === 0) {
      toast.error('Selecciona al menos un ticket para imprimir');
      return;
    }
    setTicketsToPrintBatch(ticketsToPrint);
    setTimeout(handleBatchPrint, 100);
  };

  const toggleTicketSelection = (ticketId: string) => {
    const newSet = new Set(selectedTicketsForBatchPrint);
    if (newSet.has(ticketId)) {
      newSet.delete(ticketId);
    } else {
      newSet.add(ticketId);
    }
    setSelectedTicketsForBatchPrint(newSet);
  };

  const selectAllTickets = () => {
    const allIds = new Set(filteredTickets.map(t => t.id));
    setSelectedTicketsForBatchPrint(allIds);
  };

  const deselectAllTickets = () => {
    setSelectedTicketsForBatchPrint(new Set());
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Código copiado al portapapeles');
  };

  const shareWhatsApp = (ticket: TicketData) => {
    const ssid = tenant?.settings?.ssid || ticket.node?.config?.ssid || 'JADSlink WiFi';
    const message = `Tu ticket de acceso WiFi:\n\nCódigo: ${ticket.code}\nRed: ${ssid}\nPlan: ${ticket.plan?.name}\nDuración: ${ticket.plan?.duration_minutes} min\n\nConéctate y disfruta!`;
    window.open(`https://wa.me/?text=${encodeURIComponent(message)}`, '_blank');
  };

  // --- Stats ---
  const pendingTickets = allTickets?.filter(t => t.status === 'pending').length || 0;
  const activeTickets = allTickets?.filter(t => t.status === 'active').length || 0;
  const usedTickets = allTickets?.filter(t => t.status === 'used').length || 0;
  const expiredTickets = allTickets?.filter(t => t.status === 'expired').length || 0;
  const revokedTickets = allTickets?.filter(t => t.status === 'revoked').length || 0;
  const totalRevenue = allTickets?.filter(t => t.status !== 'pending').reduce((sum, t) => sum + (t.plan?.price_usd || 0), 0) || 0;

  // --- Filters ---
  const filteredTickets = allTickets?.filter(ticket => {
    const matchesSearch =
      ticket.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ticket.node?.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ticket.plan?.name.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = statusFilter === 'all' || ticket.status === statusFilter;

    return matchesSearch && matchesStatus;
  }) || [];

  const getStatusVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (status) {
      case 'active': return 'default';
      case 'pending': return 'outline';
      case 'used': return 'secondary';
      case 'expired': return 'destructive';
      case 'revoked': return 'destructive';
      default: return 'outline';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle className="h-4 w-4" />;
      case 'pending': return <Clock className="h-4 w-4" />;
      case 'used': return <CheckCircle className="h-4 w-4" />;
      case 'expired': return <XCircle className="h-4 w-4" />;
      case 'revoked': return <Ban className="h-4 w-4" />;
      default: return <AlertCircle className="h-4 w-4" />;
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

  const isLoading = isLoadingNodes || isLoadingPlans;

  return (
    <div className="space-y-6">
      {/* Global Print Styles */}
      <style type="text/css">{`
        @media print {
          @page {
            size: A4 portrait;
            margin: 0.5cm;
          }
          body {
            print-color-adjust: exact;
            -webkit-print-color-adjust: exact;
          }
          * {
            print-color-adjust: exact;
            -webkit-print-color-adjust: exact;
          }
        }
      `}</style>

      <div>
        <h2 className="text-3xl font-bold tracking-tight">Tickets</h2>
        <p className="text-muted-foreground">
          Genera y gestiona tickets de acceso WiFi para tus usuarios
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
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
          title="Revocados"
          value={revokedTickets}
          description="Cancelados"
          icon={Ban}
          loading={isLoadingAllTickets}
        />
        <StatCard
          title="Ingresos"
          value={`$${totalRevenue.toFixed(2)}`}
          description="Total vendido"
          icon={DollarSign}
          loading={isLoadingAllTickets}
        />
      </div>

      {/* Tabs */}
      <Tabs defaultValue="generate" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="generate">Generar Tickets</TabsTrigger>
          <TabsTrigger value="view">Ver Todos ({allTickets?.length || 0})</TabsTrigger>
        </TabsList>

        {/* Generate Tab */}
        <TabsContent value="generate" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Generar Nuevos Tickets</CardTitle>
              <CardDescription>Crea tickets de acceso WiFi para vender a tus clientes</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="node">Nodo / Ubicación</Label>
                    <select
                      id="node"
                      value={selectedNode}
                      onChange={(e) => setSelectedNode(e.target.value)}
                      className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      disabled={isLoading}
                    >
                      <option value="">{isLoading ? 'Cargando...' : 'Selecciona un Nodo'}</option>
                      {nodes?.map((node) => (
                        <option key={node.id} value={node.id}>
                          {node.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="plan">Plan de Tiempo</Label>
                    <select
                      id="plan"
                      value={selectedPlan}
                      onChange={(e) => setSelectedPlan(e.target.value)}
                      className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      disabled={isLoading}
                    >
                      <option value="">{isLoading ? 'Cargando...' : 'Selecciona un Plan'}</option>
                      {plans?.map((plan) => (
                        <option key={plan.id} value={plan.id}>
                          {plan.name} - {plan.duration_minutes}min - ${plan.price_usd}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="quantity">Cantidad</Label>
                    <Input
                      id="quantity"
                      type="number"
                      min="1"
                      max="100"
                      value={quantity}
                      onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
                      disabled={generateTicketsMutation.isPending}
                    />
                  </div>
                </div>
                <Button
                  type="submit"
                  disabled={generateTicketsMutation.isPending || isLoading}
                  className="w-full md:w-auto"
                >
                  {generateTicketsMutation.isPending ? 'Generando...' : `Generar ${quantity} Ticket${quantity > 1 ? 's' : ''}`}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Generated Tickets Display */}
          {generateTicketsMutation.isSuccess && generatedTickets.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Tickets Generados Recientemente</CardTitle>
                <CardDescription>{generatedTickets.length} ticket(s) listos para usar</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {generatedTickets.map((ticket) => {
                    const node = nodes?.find(n => n.id === selectedNode);
                    const plan = plans?.find(p => p.id === selectedPlan);

                    return (
                      <div key={ticket.id} className="border rounded-lg p-4 space-y-3 bg-gradient-to-br from-blue-50 to-white">
                        <div className="flex items-center justify-between">
                          <Badge variant="outline" className="bg-white">
                            {plan?.name}
                          </Badge>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => copyToClipboard(ticket.code)}
                          >
                            <Copy className="h-4 w-4" />
                          </Button>
                        </div>

                        {ticket.qr_base64_png && (
                          <img
                            src={ticket.qr_base64_png}
                            alt={`QR ${ticket.code}`}
                            className="w-full h-48 object-contain bg-white rounded p-2"
                          />
                        )}

                        <div className="bg-white rounded p-2 text-center">
                          <p className="text-xs text-gray-600 mb-1">Código</p>
                          <p className="font-mono font-bold text-lg tracking-wider">{ticket.code}</p>
                        </div>

                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div className="bg-white rounded p-2">
                            <p className="text-gray-600">Red WiFi</p>
                            <p className="font-semibold">{tenant?.settings?.ssid || node?.config?.ssid || 'JADSlink WiFi'}</p>
                          </div>
                          {plan && (
                            <div className="bg-white rounded p-2">
                              <p className="text-gray-600">Duración</p>
                              <p className="font-semibold">{plan.duration_minutes}min</p>
                            </div>
                          )}
                        </div>

                        <Button
                          variant="default"
                          size="sm"
                          className="w-full"
                          onClick={() => triggerPrint(ticket)}
                        >
                          <Printer className="h-4 w-4 mr-2" />
                          Imprimir Ticket
                        </Button>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* View All Tab */}
        <TabsContent value="view" className="space-y-6">
          {/* Filters */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Filtros</CardTitle>
                {selectedTicketsForBatchPrint.size > 0 && (
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={deselectAllTickets}
                    >
                      Deseleccionar todos
                    </Button>
                    <Button
                      variant="default"
                      size="sm"
                      onClick={triggerBatchPrint}
                    >
                      <Printer className="h-4 w-4 mr-2" />
                      Imprimir {selectedTicketsForBatchPrint.size} ticket(s)
                    </Button>
                  </div>
                )}
              </div>
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
                  {(['all', 'pending', 'active', 'used', 'expired', 'revoked'] as const).map((status) => (
                    <Button
                      key={status}
                      variant={statusFilter === status ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setStatusFilter(status)}
                    >
                      {status === 'all' ? 'Todos' : status.charAt(0).toUpperCase() + status.slice(1)}
                    </Button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Tickets Table */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Lista de Tickets</CardTitle>
                  <CardDescription>
                    {filteredTickets.length} de {allTickets?.length || 0} ticket(s)
                    {selectedTicketsForBatchPrint.size > 0 && (
                      <span className="ml-2 text-primary font-medium">
                        ({selectedTicketsForBatchPrint.size} seleccionados)
                      </span>
                    )}
                  </CardDescription>
                </div>
                {filteredTickets.length > 0 && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={selectedTicketsForBatchPrint.size === filteredTickets.length ? deselectAllTickets : selectAllTickets}
                  >
                    {selectedTicketsForBatchPrint.size === filteredTickets.length ? 'Deseleccionar todos' : 'Seleccionar todos'}
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {isLoadingAllTickets ? (
                <div className="text-center py-8">
                  <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent" />
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
                        <TableHead className="w-12"></TableHead>
                        <TableHead>Código</TableHead>
                        <TableHead>Estado</TableHead>
                        <TableHead>Nodo</TableHead>
                        <TableHead>Plan</TableHead>
                        <TableHead>Precio</TableHead>
                        <TableHead>Creado</TableHead>
                        <TableHead className="text-right">Acciones</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredTickets.map((ticket) => (
                        <TableRow key={ticket.id}>
                          <TableCell>
                            <input
                              type="checkbox"
                              checked={selectedTicketsForBatchPrint.has(ticket.id)}
                              onChange={() => toggleTicketSelection(ticket.id)}
                              className="h-4 w-4 rounded border-gray-300"
                            />
                          </TableCell>
                          <TableCell className="font-mono font-medium">
                            {ticket.code}
                          </TableCell>
                          <TableCell>
                            <Badge variant={getStatusVariant(ticket.status)} className="flex items-center gap-1 w-fit">
                              {getStatusIcon(ticket.status)}
                              {ticket.status}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div>
                              <p className="font-medium">{ticket.node?.name || 'N/A'}</p>
                              <p className="text-xs text-muted-foreground flex items-center gap-1">
                                <Wifi className="h-3 w-3" />
                                {tenant?.settings?.ssid || ticket.node?.config?.ssid || 'JADSlink WiFi'}
                              </p>
                            </div>
                          </TableCell>
                          <TableCell>
                            {ticket.plan?.name || 'N/A'}
                            {ticket.plan && (
                              <p className="text-xs text-muted-foreground">
                                {ticket.plan.duration_minutes}min
                              </p>
                            )}
                          </TableCell>
                          <TableCell>
                            ${ticket.plan?.price_usd.toFixed(2) || '0.00'}
                          </TableCell>
                          <TableCell className="text-sm">
                            {new Date(ticket.created_at).toLocaleString('es-VE', {
                              dateStyle: 'short',
                              timeStyle: 'short'
                            })}
                          </TableCell>
                          <TableCell className="text-right">
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="sm">
                                  <MoreVertical className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuLabel>Acciones</DropdownMenuLabel>
                                <DropdownMenuItem onClick={() => {
                                  setSelectedTicketForView(ticket);
                                  setViewDialogOpen(true);
                                }}>
                                  <Eye className="h-4 w-4 mr-2" />
                                  Ver Detalles
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => triggerPrint(ticket)}>
                                  <Printer className="h-4 w-4 mr-2" />
                                  Imprimir
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => copyToClipboard(ticket.code)}>
                                  <Copy className="h-4 w-4 mr-2" />
                                  Copiar Código
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => shareWhatsApp(ticket)}>
                                  <Share2 className="h-4 w-4 mr-2" />
                                  Compartir WhatsApp
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                {(ticket.status === 'pending' || ticket.status === 'active') && (
                                  <DropdownMenuItem
                                    className="text-destructive"
                                    onClick={() => {
                                      setTicketToRevoke(ticket);
                                      setRevokeDialogOpen(true);
                                    }}
                                  >
                                    <Ban className="h-4 w-4 mr-2" />
                                    Revocar
                                  </DropdownMenuItem>
                                )}
                              </DropdownMenuContent>
                            </DropdownMenu>
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

      {/* View Details Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Detalles del Ticket</DialogTitle>
            <DialogDescription>Información completa del ticket de acceso</DialogDescription>
          </DialogHeader>
          {selectedTicketForView && (
            <div className="space-y-4">
              {selectedTicketForView.qr_base64_png && (
                <div className="flex justify-center">
                  <img
                    src={selectedTicketForView.qr_base64_png}
                    alt={`QR ${selectedTicketForView.code}`}
                    className="w-48 h-48"
                  />
                </div>
              )}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Código:</span>
                  <span className="font-mono font-bold">{selectedTicketForView.code}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Estado:</span>
                  <Badge variant={getStatusVariant(selectedTicketForView.status)}>
                    {selectedTicketForView.status}
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Nodo:</span>
                  <span className="font-medium">{selectedTicketForView.node?.name || 'N/A'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Red WiFi:</span>
                  <span className="font-medium">{tenant?.settings?.ssid || selectedTicketForView.node?.config?.ssid || 'JADSlink WiFi'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Plan:</span>
                  <span className="font-medium">{selectedTicketForView.plan?.name || 'N/A'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Duración:</span>
                  <span className="font-medium">{selectedTicketForView.plan?.duration_minutes || 0} min</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Precio:</span>
                  <span className="font-medium">${selectedTicketForView.plan?.price_usd.toFixed(2) || '0.00'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Creado:</span>
                  <span className="text-sm">{new Date(selectedTicketForView.created_at).toLocaleString('es-VE')}</span>
                </div>
                {selectedTicketForView.activated_at && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Activado:</span>
                    <span className="text-sm">{new Date(selectedTicketForView.activated_at).toLocaleString('es-VE')}</span>
                  </div>
                )}
                {selectedTicketForView.expires_at && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Expira:</span>
                    <span className="text-sm">{new Date(selectedTicketForView.expires_at).toLocaleString('es-VE')}</span>
                  </div>
                )}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => triggerPrint(selectedTicketForView)}
                >
                  <Printer className="h-4 w-4 mr-2" />
                  Imprimir
                </Button>
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => shareWhatsApp(selectedTicketForView)}
                >
                  <Share2 className="h-4 w-4 mr-2" />
                  Compartir
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Revoke Confirmation Dialog */}
      <AlertDialog open={revokeDialogOpen} onOpenChange={setRevokeDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Revocar este ticket?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta acción marcará el ticket como revocado y no podrá ser usado.
              {ticketToRevoke && (
                <span className="block mt-2 font-mono font-bold">
                  Código: {ticketToRevoke.code}
                </span>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel
              onClick={() => {
                setRevokeDialogOpen(false);
                setTicketToRevoke(null);
              }}
            >
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={() => ticketToRevoke && revokeTicketMutation.mutate(ticketToRevoke.id)}
              disabled={revokeTicketMutation.isPending}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {revokeTicketMutation.isPending ? 'Revocando...' : 'Revocar Ticket'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Hidden Printable Component - Single */}
      <div style={{ display: "none" }}>
        {selectedTicketForPrint && (
          <PrintableTicket
            ref={ticketToPrintRef}
            ticket={selectedTicketForPrint}
            tenant={tenant}
            node={nodes?.find(n => n.id === ('node' in selectedTicketForPrint ? selectedTicketForPrint.node?.id : selectedNode))}
            plan={plans?.find(p => p.id === ('plan' in selectedTicketForPrint ? selectedTicketForPrint.plan?.id : selectedPlan))}
          />
        )}
      </div>

      {/* Hidden Printable Component - Batch (3 per page) */}
      <div style={{ display: "none" }}>
        <div ref={batchPrintRef} className="space-y-4 p-4">
          {ticketsToPrintBatch.map((ticket, index) => {
            const isLastInPage = (index + 1) % 3 === 0;
            const isLast = index === ticketsToPrintBatch.length - 1;

            return (
              <div key={ticket.id} style={{ pageBreakAfter: isLastInPage && !isLast ? 'always' : 'auto', marginBottom: isLastInPage ? 0 : '1rem' }}>
                <PrintableTicket
                  ticket={ticket}
                  tenant={tenant}
                  node={nodes?.find(n => n.id === ticket.node?.id)}
                  plan={plans?.find(p => p.id === ticket.plan?.id)}
                />
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default Tickets;
