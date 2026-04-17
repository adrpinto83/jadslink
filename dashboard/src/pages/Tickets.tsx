
import React, { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useReactToPrint } from 'react-to-print';

// --- Type Definitions ---
interface Node {
  id: string;
  name: string;
}

interface Plan {
  id: string;
  name: string;
  duration_minutes: number;
}

interface Tenant {
    id: string;
    name: string;
    settings: {
        logo_url?: string;
    }
}

interface GeneratedTicket {
  id: string;
  code: string;
  qr_data: string; // URL for the user to scan
  qr_base64_png?: string; // Base64 data for display
}

// --- Printable Ticket Component ---
const PrintableTicket = React.forwardRef<HTMLDivElement, { ticket: GeneratedTicket, tenant: Tenant | undefined }>(({ ticket, tenant }, ref) => (
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

  // --- State Management ---
  const [selectedNode, setSelectedNode] = useState<string>('');
  const [selectedPlan, setSelectedPlan] = useState<string>('');
  const [quantity, setQuantity] = useState<number>(1);
  const [generatedTickets, setGeneratedTickets] = useState<GeneratedTicket[]>([]);
  
  const ticketToPrintRef = useRef<HTMLDivElement>(null);
  const [selectedTicketForPrint, setSelectedTicketForPrint] = useState<GeneratedTicket | null>(null);

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

  // --- Mutations ---
  const generateTicketsMutation = useMutation<GeneratedTicket[], Error, { node_id: string; plan_id: string; quantity: number }>({
    mutationFn: async (data) => {
      const response = await apiClient.post('/tickets/generate', data);
      return response.data;
    },
    onSuccess: (newTickets) => {
      setGeneratedTickets(newTickets);
      queryClient.invalidateQueries({ queryKey: ['all-tickets'] });
    },
    onError: (error) => {
      alert(`Error generating tickets: ${error.message}`);
    }
  });

  // --- Print Handler ---
  const handlePrint = useReactToPrint({
    contentRef: ticketToPrintRef,
  });

  const triggerPrint = (ticket: GeneratedTicket) => {
      setSelectedTicketForPrint(ticket);
      setTimeout(handlePrint, 50); // Small delay to allow state to update before printing
  }

  // --- Event Handlers ---
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedNode || !selectedPlan || quantity < 1) {
      alert('Please select a node, a plan, and enter a valid quantity.');
      return;
    }
    generateTicketsMutation.mutate({ node_id: selectedNode, plan_id: selectedPlan, quantity });
  };

  const isLoading = isLoadingNodes || isLoadingPlans;

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Generate Tickets</h1>

      <Card className="p-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label htmlFor="node">Node</Label>
              <select id="node" value={selectedNode} onChange={(e) => setSelectedNode(e.target.value)} className="w-full p-2 border rounded mt-1" disabled={isLoading}>
                <option value="">{isLoading ? 'Loading...' : 'Select a Node'}</option>
                {nodes?.map((node) => <option key={node.id} value={node.id}>{node.name}</option>)}
              </select>
            </div>
            <div>
              <Label htmlFor="plan">Plan</Label>
              <select id="plan" value={selectedPlan} onChange={(e) => setSelectedPlan(e.target.value)} className="w-full p-2 border rounded mt-1" disabled={isLoading}>
                <option value="">{isLoading ? 'Loading...' : 'Select a Plan'}</option>
                {plans?.map((plan) => <option key={plan.id} value={plan.id}>{plan.name} ({plan.duration_minutes} min)</option>)}
              </select>
            </div>
            <div>
              <Label htmlFor="quantity">Quantity</Label>
              <Input id="quantity" type="number" min="1" max="50" value={quantity} onChange={(e) => setQuantity(parseInt(e.target.value))} disabled={generateTicketsMutation.isPending} className="mt-1" />
            </div>
          </div>
          <Button type="submit" disabled={generateTicketsMutation.isPending || isLoading}>
            {generateTicketsMutation.isPending ? 'Generating...' : 'Generate Tickets'}
          </Button>
        </form>
      </Card>

      {generateTicketsMutation.isSuccess && (
        <Card className="p-6">
          <h2 className="text-2xl font-semibold mb-4">Generated Tickets</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {generatedTickets.map((ticket) => (
              <div key={ticket.id} className="p-4 border rounded-lg text-center space-y-2">
                <p className="font-mono text-lg font-bold">{ticket.code}</p>
                {ticket.qr_base64_png ? (
                    <img src={ticket.qr_base64_png} alt={`QR Code for ${ticket.code}`} className="w-48 h-48 mx-auto" />
                ) : (
                    <div className="w-48 h-48 bg-gray-200 flex items-center justify-center mx-auto text-sm text-gray-500">No QR Image</div>
                )}
                <Button variant="outline" size="sm" onClick={() => triggerPrint(ticket)}>Print</Button>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Hidden component for printing */}
      <div style={{ display: "none" }}>
        {selectedTicketForPrint && <PrintableTicket ref={ticketToPrintRef} ticket={selectedTicketForPrint} tenant={tenant} />}
      </div>
    </div>
  );
};

export default Tickets;
