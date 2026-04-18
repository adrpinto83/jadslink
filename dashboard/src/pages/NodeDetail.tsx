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
  } | null;
}

// Schema for the form
const formSchema = z.object({
  name: z.string().min(3, 'El nombre debe tener al menos 3 caracteres'),
  ssid: z.string().optional(),
  channel: z.coerce.number().int().min(1).max(13).optional(),
  max_clients: z.coerce.number().int().min(1).optional(),
  bandwidth_default: z.coerce.number().int().min(0).optional(),
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
                  <Button type="submit" disabled={mutation.isPending}>
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
