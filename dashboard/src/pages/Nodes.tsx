import React from 'react';
import { useQuery } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import NodeMap from '@/components/NodeMap';

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

const fetchNodes = async (): Promise<Node[]> => {
  const response = await apiClient.get('/nodes');
  return response.data;
};

const Nodes: React.FC = () => {
  const { data: nodes, isLoading, error } = useQuery<Node[], Error>({ 
    queryKey: ['nodes'], 
    queryFn: fetchNodes 
  });

  const getStatusVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (status.toLowerCase()) {
      case 'online':
        return 'default'; // Green-ish in default theme
      case 'offline':
        return 'destructive';
      default:
        return 'secondary';
    }
  };

  if (isLoading) return <div>Cargando nodos...</div>;
  if (error) return <div>Error al cargar nodos: {error.message}</div>;

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold">Nodos</h2>
      
      <Card>
        <CardHeader>
          <CardTitle>Mapa de Nodos</CardTitle>
        </CardHeader>
        <CardContent className="h-96 p-0">
          {nodes && <NodeMap nodes={nodes} />}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Lista de Nodos</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nombre</TableHead>
                <TableHead>Serial</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead>Última vez visto</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {nodes?.map((node) => (
                <TableRow key={node.id}>
                  <TableCell>{node.name}</TableCell>
                  <TableCell>{node.serial}</TableCell>
                  <TableCell>
                    <Badge variant={getStatusVariant(node.status)}>{node.status}</Badge>
                  </TableCell>
                  <TableCell>{node.last_seen_at ? new Date(node.last_seen_at).toLocaleString() : 'Nunca'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default Nodes;
