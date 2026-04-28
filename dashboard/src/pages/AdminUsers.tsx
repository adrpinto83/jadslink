import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Users, Mail, Trash2, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

interface TeamMember {
  id: string;
  email: string;
  full_name: string | null;
  tenant_role: string;
  is_active: boolean;
  created_at: string;
}

interface EmployeeListResponse {
  members: TeamMember[];
  total_count: number;
  role_counts: Record<string, number>;
}

interface Tenant {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
}

const ROLE_LABELS: Record<string, { label: string; color: string; description: string }> = {
  owner: { label: 'Propietario', color: 'bg-purple-100 text-purple-800', description: 'Control total de la cuenta' },
  admin: { label: 'Administrador', color: 'bg-blue-100 text-blue-800', description: 'Gestión de equipo y configuración' },
  collaborator: { label: 'Colaborador', color: 'bg-green-100 text-green-800', description: 'Acceso de lectura/escritura completo' },
  viewer: { label: 'Visualizador', color: 'bg-gray-100 text-gray-800', description: 'Solo lectura' },
};

const AdminUsers: React.FC = () => {
  const [selectedTenantId, setSelectedTenantId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // Obtener lista de tenants
  const { data: tenants, isLoading: tenantsLoading } = useQuery<Tenant[]>({
    queryKey: ['admin', 'tenants'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/tenants');
      return response.data;
    },
  });

  // Obtener empleados del tenant seleccionado
  const { data: teamData, isLoading: employeesLoading } = useQuery<EmployeeListResponse>({
    queryKey: ['admin', 'tenants', selectedTenantId, 'employees'],
    queryFn: async () => {
      if (!selectedTenantId) return null;
      const response = await apiClient.get(`/admin/tenants/${selectedTenantId}/employees`);
      return response.data;
    },
    enabled: !!selectedTenantId,
  });

  // Cambiar rol
  const changeRoleMutation = useMutation({
    mutationFn: async (data: { userId: string; role: string }) => {
      if (!selectedTenantId) throw new Error('Tenant no seleccionado');
      await apiClient.patch(`/admin/tenants/${selectedTenantId}/employees/${data.userId}`, {
        tenant_role: data.role,
      });
    },
    onSuccess: () => {
      toast.success('Rol actualizado');
      if (selectedTenantId) {
        queryClient.invalidateQueries({ queryKey: ['admin', 'tenants', selectedTenantId, 'employees'] });
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Error al cambiar rol');
    },
  });

  // Remover empleado
  const removeMutation = useMutation({
    mutationFn: async (userId: string) => {
      if (!selectedTenantId) throw new Error('Tenant no seleccionado');
      await apiClient.delete(`/admin/tenants/${selectedTenantId}/employees/${userId}`);
    },
    onSuccess: () => {
      toast.success('Empleado removido');
      if (selectedTenantId) {
        queryClient.invalidateQueries({ queryKey: ['admin', 'tenants', selectedTenantId, 'employees'] });
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Error al remover empleado');
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Gestión de Empleados</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">Administra empleados de cualquier operador</p>
      </div>

      {/* Selector de Tenant */}
      <Card>
        <CardHeader>
          <CardTitle>Seleccionar Operador</CardTitle>
          <CardDescription>Elige un operador para gestionar sus empleados</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Label htmlFor="tenant-select">Operador/Tenant</Label>
            <Select value={selectedTenantId || ''} onValueChange={setSelectedTenantId}>
              <SelectTrigger id="tenant-select">
                <SelectValue placeholder="Selecciona un operador..." />
              </SelectTrigger>
              <SelectContent>
                {tenantsLoading ? (
                  <div className="p-2 text-sm text-gray-500">Cargando...</div>
                ) : !tenants || tenants.length === 0 ? (
                  <div className="p-2 text-sm text-gray-500">No hay operadores</div>
                ) : (
                  tenants.map((tenant) => (
                    <SelectItem key={tenant.id} value={tenant.id}>
                      <div className="flex items-center gap-2">
                        <span>{tenant.name}</span>
                        {!tenant.is_active && (
                          <Badge variant="outline" className="text-xs">
                            Inactivo
                          </Badge>
                        )}
                      </div>
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Empleados del Tenant Seleccionado */}
      {selectedTenantId && (
        <>
          {/* Estadísticas */}
          {teamData && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(teamData.role_counts).map(([role, count]) => (
                <Card key={role} className="p-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold">{count}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400 capitalize">
                      {ROLE_LABELS[role]?.label}
                    </p>
                  </div>
                </Card>
              ))}
            </div>
          )}

          {/* Listado de Empleados */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5" />
                Miembros del Equipo
              </CardTitle>
              <CardDescription>{teamData?.total_count || 0} miembro(s)</CardDescription>
            </CardHeader>
            <CardContent>
              {employeesLoading ? (
                <div className="flex items-center justify-center py-8">
                  <p className="text-gray-500">Cargando miembros...</p>
                </div>
              ) : !teamData?.members || teamData.members.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <Users className="w-12 h-12 text-gray-400 mb-4" />
                  <p className="text-gray-600 dark:text-gray-400">No hay miembros en este equipo</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {teamData.members.map((member) => (
                    <div
                      key={member.id}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white font-semibold">
                            {(member.full_name || member.email).charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <p className="font-medium">{member.full_name || 'Sin nombre'}</p>
                            <div className="flex items-center gap-2 mt-1">
                              <p className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-1">
                                <Mail className="w-3 h-3" />
                                {member.email}
                              </p>
                              {!member.is_active && (
                                <Badge variant="outline" className="text-xs">
                                  Inactivo
                                </Badge>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        {/* Selector de rol */}
                        <Select
                          value={member.tenant_role}
                          onValueChange={(newRole) =>
                            changeRoleMutation.mutate({ userId: member.id, role: newRole })
                          }
                          disabled={member.tenant_role === 'owner' || changeRoleMutation.isPending}
                        >
                          <SelectTrigger className="w-40">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {member.tenant_role === 'owner' ? (
                              <SelectItem value="owner">
                                <div className="flex items-center gap-2">
                                  👑 Propietario
                                </div>
                              </SelectItem>
                            ) : (
                              <>
                                <SelectItem value="viewer">👁️ Visualizador</SelectItem>
                                <SelectItem value="collaborator">✎ Colaborador</SelectItem>
                                <SelectItem value="admin">⚙️ Administrador</SelectItem>
                              </>
                            )}
                          </SelectContent>
                        </Select>

                        {/* Botón remover */}
                        {member.tenant_role !== 'owner' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              if (confirm('¿Estás seguro de que deseas remover este empleado?')) {
                                removeMutation.mutate(member.id);
                              }
                            }}
                            disabled={removeMutation.isPending}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {/* Información sobre roles */}
      <Card className="bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <AlertCircle className="w-5 h-5" />
            Información sobre Roles
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Object.entries(ROLE_LABELS).map(([role, { label, description }]) => (
              <div key={role} className="flex items-start gap-3">
                <div className="flex-shrink-0 w-2 h-2 rounded-full mt-2 bg-blue-600"></div>
                <div>
                  <p className="font-semibold text-sm">{label}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{description}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminUsers;
