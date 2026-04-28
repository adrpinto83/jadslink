// @ts-nocheck
import React from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { useAuthStore } from '@/stores/auth';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { toast } from 'sonner';

// Define the full Node type, including config
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
  config: {
    ssid: string;
    channel: number;
    max_clients: number;
    bandwidth_default: number;
    api_endpoint?: string;
    heartbeat_interval?: number;
    metrics_interval?: number;
    enable_metrics?: boolean;
  } | null;
}

// Schema for the form
const formSchema = z.object({
  name: z.string().min(3, 'El nombre debe tener al menos 3 caracteres'),
  ssid: z.string().optional(),
  channel: z.coerce.number().int().min(1).max(13).optional(),
  max_clients: z.coerce.number().int().min(1).optional(),
  bandwidth_default: z.coerce.number().int().min(0).optional(),
  api_endpoint: z.string().url().optional(),
  heartbeat_interval: z.coerce.number().int().min(10).max(300).optional(),
  metrics_interval: z.coerce.number().int().min(30).max(600).optional(),
  enable_metrics: z.boolean().optional(),
});

type FormValues = z.infer<typeof formSchema>;

const fetchNode = async (nodeId: string): Promise<Node> => {
  const response = await apiClient.get(`/nodes/${nodeId}`);
  return response.data;
};

const NodeDetail: React.FC = () => {
  const { nodeId } = useParams<{ nodeId: string }>();
  const queryClient = useQueryClient();
  const { user } = useAuthStore();

  const { data: node, isLoading, error } = useQuery<Node, Error>({
    queryKey: ['node', nodeId],
    queryFn: () => fetchNode(nodeId!),
    enabled: !!nodeId,
  });

  const mutation = useMutation<void, Error, FormValues>({
    mutationFn: (updatedNode: FormValues) => {
        const payload = {
          name: updatedNode.name,
          config: {
            ssid: updatedNode.ssid,
            channel: updatedNode.channel,
            max_clients: updatedNode.max_clients,
            bandwidth_default: updatedNode.bandwidth_default,
            api_endpoint: updatedNode.api_endpoint || 'https://api.jadslink.io',
            heartbeat_interval: updatedNode.heartbeat_interval || 30,
            metrics_interval: updatedNode.metrics_interval || 60,
            enable_metrics: updatedNode.enable_metrics !== false,
          }
        }
        return apiClient.patch(`/nodes/${nodeId}`, payload);
    },
    onSuccess: () => {
        toast.success('Nodo actualizado exitosamente');
        queryClient.invalidateQueries({ queryKey: ['node', nodeId] });
        queryClient.invalidateQueries({ queryKey: ['nodes'] });
    },
    onError: (error) => {
        toast.error(`Error al actualizar el nodo: ${error.message}`);
    }
  });

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
        name: '',
        ssid: '',
        channel: 1,
        max_clients: 10,
        bandwidth_default: 0,
        api_endpoint: 'https://api.jadslink.io',
        heartbeat_interval: 30,
        metrics_interval: 60,
        enable_metrics: true,
    }
  });

  React.useEffect(() => {
    if (node) {
      form.reset({
        name: node.name,
        ssid: node.config?.ssid ?? '',
        channel: node.config?.channel ?? 1,
        max_clients: node.config?.max_clients ?? 10,
        bandwidth_default: node.config?.bandwidth_default ?? 0,
        api_endpoint: node.config?.api_endpoint ?? 'https://api.jadslink.io',
        heartbeat_interval: node.config?.heartbeat_interval ?? 30,
        metrics_interval: node.config?.metrics_interval ?? 60,
        enable_metrics: node.config?.enable_metrics ?? true,
      });
    }
  }, [node, form]);

  const onSubmit = (values: FormValues) => {
    mutation.mutate(values);
  };

  if (isLoading) return <div>Cargando detalles del nodo...</div>;
  if (error) return <div>Error al cargar el nodo: {error.message}</div>;
  if (!node) return <div>Nodo no encontrado.</div>;

  const isAdmin = user?.role === 'superadmin';

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold">{node.name}</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Información del Nodo</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p><strong>Serial:</strong> {node.serial}</p>
            <p><strong>Estado:</strong> {node.status}</p>
            <p><strong>Última vez visto:</strong> {node.last_seen_at ? new Date(node.last_seen_at).toLocaleString() : 'Nunca'}</p>
          </CardContent>
        </Card>
        
        {isAdmin && (
          <Card>
            <CardHeader>
              <CardTitle>Configuración</CardTitle>
              <CardDescription>
                Editable solo por administradores.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
                  <FormField
                    control={form.control}
                    name="name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Nombre del Nodo</FormLabel>
                        <FormControl>
                          <Input {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="ssid"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>SSID</FormLabel>
                        <FormControl>
                          <Input {...field} />
                        </FormControl>
                        <FormDescription>El nombre de la red WiFi que verán los usuarios.</FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="channel"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Canal WiFi</FormLabel>
                        <FormControl>
                          <Input type="number" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="max_clients"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Máximo de Clientes</FormLabel>
                        <FormControl>
                          <Input type="number" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                   <FormField
                    control={form.control}
                    name="bandwidth_default"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Ancho de banda por defecto (kbps)</FormLabel>
                        <FormControl>
                          <Input type="number" {...field} />
                        </FormControl>
                        <FormDescription>0 para ilimitado.</FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {/* Router Communication Section */}
                  <div className="border-t pt-6">
                    <h3 className="font-semibold text-base mb-4">Comunicación del Router</h3>

                    <FormField
                      control={form.control}
                      name="api_endpoint"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>API Endpoint</FormLabel>
                          <FormControl>
                            <Input {...field} placeholder="https://api.jadslink.io" />
                          </FormControl>
                          <FormDescription>URL del servidor backend para sincronización</FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <div className="grid grid-cols-2 gap-4 mt-4">
                      <FormField
                        control={form.control}
                        name="heartbeat_interval"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Intervalo Heartbeat (seg)</FormLabel>
                            <FormControl>
                              <Input type="number" {...field} min="10" max="300" />
                            </FormControl>
                            <FormDescription>Frecuencia de latidos (10-300)</FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="metrics_interval"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Intervalo Métricas (seg)</FormLabel>
                            <FormControl>
                              <Input type="number" {...field} min="30" max="600" />
                            </FormControl>
                            <FormDescription>Frecuencia de reportes (30-600)</FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>

                    <FormField
                      control={form.control}
                      name="enable_metrics"
                      render={({ field }) => (
                        <FormItem className="flex items-center gap-3 mt-4 p-3 bg-muted rounded">
                          <FormControl>
                            <input
                              type="checkbox"
                              checked={field.value}
                              onChange={field.onChange}
                              className="rounded"
                            />
                          </FormControl>
                          <FormLabel className="mb-0 cursor-pointer flex-1">Reportar métricas al servidor</FormLabel>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <Button type="submit" disabled={mutation.isPending} className="mt-6">
                    {mutation.isPending ? 'Guardando...' : 'Guardar Cambios'}
                  </Button>
                </form>
              </Form>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default NodeDetail;
