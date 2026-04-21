import React, { useState, useRef, useEffect, useCallback } from 'react';
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
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useReactToPrint } from 'react-to-print';
import { toast } from 'sonner';
import {
  Search,
  Printer,
  CheckCircle,
  Clock,
  XCircle,
  Copy,
  Ban,
  MoreVertical,
  Wifi,
  DollarSign,
  Share2,
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
  plan_name: string;
  tenant_logo_url: string | null;
  tenant_ssid: string | null;
}

// --- Compact Printable Ticket Component ---
const PrintableTicket = React.forwardRef<HTMLDivElement, {
  ticket: GeneratedTicket | TicketData;
  tenant: Tenant | undefined;
  showQr: boolean;
}>(({ ticket, tenant, showQr }, ref) => {
  const ssid = 'tenant_ssid' in ticket && ticket.tenant_ssid ? ticket.tenant_ssid : tenant?.settings?.ssid || 'JADSlink WiFi';
  const logoUrl = 'tenant_logo_url' in ticket && ticket.tenant_logo_url ? ticket.tenant_logo_url : tenant?.settings?.logo_url;
  const planName = 'plan_name' in ticket ? ticket.plan_name : ('plan' in ticket ? ticket.plan?.name : 'N/A');

  return (
    <div ref={ref} className="printable-ticket bg-white p-3 border border-dashed border-gray-400 rounded-lg w-full">
      <div className="flex items-center justify-between pb-2 mb-2 border-b border-dashed">
        <div className="flex items-center gap-2">
          {logoUrl ? (
            <img src={logoUrl} alt={tenant?.name} className="h-8 w-auto max-w-[100px]" />
          ) : (
            <Wifi className="h-6 w-6 text-blue-600" />
          )}
          <h2 className="text-md font-bold text-gray-800">{tenant?.name || 'JADSlink'}</h2>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-500">Plan</p>
          <p className="font-semibold text-sm">{planName}</p>
        </div>
      </div>

      <div className={`grid gap-2 ${showQr ? 'grid-cols-2' : 'grid-cols-1'}`}>
        {showQr && ticket.qr_base64_png && (
          <div className="flex flex-col items-center justify-center">
            <img
              src={ticket.qr_base64_png}
              alt={`QR ${ticket.code}`}
              className="w-24 h-24 object-contain"
              style={{ imageRendering: 'pixelated' }}
            />
          </div>
        )}

        <div className="flex flex-col justify-center space-y-2">
          <div>
            <p className="text-xs text-gray-600">Red WiFi:</p>
            <p className="font-bold text-lg">{ssid}</p>
          </div>
          <div>
            <p className="text-xs text-gray-600">Código de Acceso:</p>
            <p className="font-mono text-xl font-bold tracking-wider bg-gray-100 px-2 py-1 rounded border-gray-300 border">{ticket.code}</p>
          </div>
        </div>
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
  const [batchRevokeDialogOpen, setBatchRevokeDialogOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'pending' | 'active' | 'used' | 'expired' | 'revoked'>('all');
  const [selectedTicketsForBatchPrint, setSelectedTicketsForBatchPrint] = useState<Set<string>>(new Set());
  const [ticketsToPrintBatch, setTicketsToPrintBatch] = useState<TicketData[]>([]);
  const [showQrInPrint, setShowQrInPrint] = useState(true);

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

  const revokeMultipleTicketsMutation = useMutation({
    mutationFn: async (ticketIds: string[]) => {
      await apiClient.post('/tickets/revoke-multiple', { ticket_ids: ticketIds });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['all-tickets'] });
      setSelectedTicketsForBatchPrint(new Set());
      setBatchRevokeDialogOpen(false);
      toast.success('Tickets seleccionados revocados exitosamente');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Error al revocar tickets en lote');
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
    content: () => ticketToPrintRef.current,
    onAfterPrint: () => setSelectedTicketForPrint(null),
  });

  const handleBatchPrint = useReactToPrint({
    content: () => batchPrintRef.current,
    onAfterPrint: () => setTicketsToPrintBatch([]),
  });

  // Effect to trigger single ticket print
  useEffect(() => {
    if (selectedTicketForPrint) {
      // Small delay to ensure DOM is ready
      const timer = setTimeout(() => {
        handlePrint();
      }, 150);
      return () => clearTimeout(timer);
    }
  }, [selectedTicketForPrint]);

  // Effect to trigger batch print
  useEffect(() => {
    if (ticketsToPrintBatch.length > 0) {
      const timer = setTimeout(() => {
        handleBatchPrint();
      }, 150);
      return () => clearTimeout(timer);
    }
  }, [ticketsToPrintBatch]);

  const triggerPrint = useCallback((ticket: GeneratedTicket | TicketData) => {
    setSelectedTicketForPrint(ticket);
  }, []);

  const triggerBatchPrint = useCallback(() => {
    const ticketsToPrint = filteredTickets.filter(t => selectedTicketsForBatchPrint.has(t.id));
    if (ticketsToPrint.length === 0) {
      toast.error('Selecciona al menos un ticket para imprimir');
      return;
    }
    setTicketsToPrintBatch(ticketsToPrint);
  }, [selectedTicketsForBatchPrint, filteredTickets]);

  const handleBatchRevoke = () => {
    revokeMultipleTicketsMutation.mutate(Array.from(selectedTicketsForBatchPrint));
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
    const message = `Tu ticket de acceso WiFi:

Código: ${ticket.code}
Red: ${ssid}
Plan: ${ticket.plan?.name || 'N/A'}
Duración: ${ticket.plan?.duration_minutes || 0} min

Conéctate y disfruta!`;
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
    const searchTermLower = searchTerm.toLowerCase();
    const matchesSearch =
      ticket.code.toLowerCase().includes(searchTermLower) ||
      (ticket.node?.name || '').toLowerCase().includes(searchTermLower) ||
      (ticket.plan?.name || '').toLowerCase().includes(searchTermLower);

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
    icon: React.ElementType;
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
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
          }
          .printable-batch-area {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            grid-template-rows: repeat(4, 1fr);
            gap: 1cm;
            height: 100%;
          }
          .printable-ticket {
            page-break-inside: avoid;
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
        <StatCard title="Pendientes" value={pendingTickets} description="Sin activar" icon={Clock} loading={isLoadingAllTickets} />
        <StatCard title="Activos" value={activeTickets} description="En uso ahora" icon={CheckCircle} loading={isLoadingAllTickets} />
        <StatCard title="Usados" value={usedTickets} description="Completados" icon={CheckCircle} loading={isLoadingAllTickets} />
        <StatCard title="Expirados" value={expiredTickets} description="Vencidos" icon={XCircle} loading={isLoadingAllTickets} />
        <StatCard title="Revocados" value={revokedTickets} description="Cancelados" icon={Ban} loading={isLoadingAllTickets} />
        <StatCard title="Ingresos" value={`$${totalRevenue.toFixed(2)}`} description="Total vendido" icon={DollarSign} loading={isLoadingAllTickets} />
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
                <CardDescription>
                  {generatedTickets.length} ticket(s) listos para usar. Puedes imprimirlos individualmente.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {generatedTickets.map((ticket) => (
                    <div key={ticket.id} className="border rounded-lg p-4 space-y-3 bg-gray-50">
                       <PrintableTicket ticket={ticket} tenant={tenant} showQr={true} />
                       <Button
                          variant="outline"
                          size="sm"
                          className="w-full"
                          onClick={() => triggerPrint(ticket)}
                        >
                          <Printer className="h-4 w-4 mr-2" />
                          Imprimir Ticket
                        </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* View All Tab */}
        <TabsContent value="view" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Lista de Tickets</CardTitle>
              <CardDescription>Busca, filtra y gestiona todos los tickets del sistema.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
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
                      {status.charAt(0).toUpperCase() + status.slice(1)}
                    </Button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
               <div className="flex flex-col md:flex-row justify-between items-center gap-4">
                  <div>
                     <CardTitle>Acciones en Lote</CardTitle>
                     <CardDescription>{selectedTicketsForBatchPrint.size} ticket(s) seleccionados</CardDescription>
                  </div>
                  <div className="flex items-center gap-4">
                     <div className="flex items-center space-x-2">
                        <input
                           type="checkbox"
                           id="show-qr-print"
                           checked={showQrInPrint}
                           onChange={(e) => setShowQrInPrint(e.target.checked)}
                           className="h-4 w-4 rounded border-gray-300"
                        />
                        <Label htmlFor="show-qr-print">Incluir QR</Label>
                     </div>
                     <Button
                        variant="default"
                        size="sm"
                        onClick={triggerBatchPrint}
                        disabled={selectedTicketsForBatchPrint.size === 0}
                        >
                        <Printer className="h-4 w-4 mr-2" />
                        Imprimir Selección
                     </Button>
                     <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => setBatchRevokeDialogOpen(true)}
                        disabled={selectedTicketsForBatchPrint.size === 0}
                        >
                        <Ban className="h-4 w-4 mr-2" />
                        Revocar Selección
                     </Button>
                  </div>
               </div>
            </CardHeader>
            <CardContent>
              {isLoadingAllTickets ? (
                <p>Cargando tickets...</p>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-12">
                          <input
                            type="checkbox"
                            onChange={(e) => e.target.checked ? selectAllTickets() : deselectAllTickets()}
                            checked={selectedTicketsForBatchPrint.size === filteredTickets.length && filteredTickets.length > 0}
                          />
                        </TableHead>
                        <TableHead>Código</TableHead>
                        <TableHead>Estado</TableHead>
                        <TableHead>Nodo</TableHead>
                        <TableHead>Plan</TableHead>
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
                          <TableCell className="font-mono font-medium">{ticket.code}</TableCell>
                          <TableCell>
                            <Badge variant={getStatusVariant(ticket.status)}>{ticket.status}</Badge>
                          </TableCell>
                          <TableCell>{ticket.node?.name}</TableCell>
                          <TableCell>{ticket.plan?.name}</TableCell>
                          <TableCell>{new Date(ticket.created_at).toLocaleDateString()}</TableCell>
                          <TableCell className="text-right">
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon"><MoreVertical className="h-4 w-4" /></Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={() => triggerPrint(ticket)}><Printer className="mr-2 h-4 w-4" /> Imprimir</DropdownMenuItem>
                                <DropdownMenuItem onClick={() => copyToClipboard(ticket.code)}><Copy className="mr-2 h-4 w-4" /> Copiar</DropdownMenuItem>
                                <DropdownMenuItem onClick={() => shareWhatsApp(ticket as TicketData)}><Share2 className="mr-2 h-4 w-4" /> Compartir</DropdownMenuItem>
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

      {/* Hidden Printable Component - Single */}
      {selectedTicketForPrint && (
        <div style={{ visibility: "hidden", height: 0, overflow: "hidden" }}>
          <div ref={ticketToPrintRef}>
            <PrintableTicket
              ticket={selectedTicketForPrint}
              tenant={tenant}
              showQr={showQrInPrint}
            />
          </div>
        </div>
      )}

      {/* Hidden Printable Component - Batch (Grid) */}
      {ticketsToPrintBatch.length > 0 && (
        <div style={{ visibility: "hidden", height: 0, overflow: "hidden" }}>
          <div ref={batchPrintRef} className="printable-batch-area">
            {ticketsToPrintBatch.map((ticket) => (
              <PrintableTicket
                key={ticket.id}
                ticket={ticket}
                tenant={tenant}
                showQr={showQrInPrint}
              />
            ))}
          </div>
        </div>
      )}

      {/* Batch Revoke Dialog */}
      <AlertDialog open={batchRevokeDialogOpen} onOpenChange={setBatchRevokeDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Revocar Tickets Seleccionados?</AlertDialogTitle>
            <AlertDialogDescription>
              Estás a punto de revocar {selectedTicketsForBatchPrint.size} tickets. Esta acción no se puede deshacer.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleBatchRevoke}
              disabled={revokeMultipleTicketsMutation.isPending}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {revokeMultipleTicketsMutation.isPending ? 'Revocando...' : 'Revocar'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default Tickets;
