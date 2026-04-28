import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { useAuthStore } from '@/stores/auth';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Users, UserPlus, Mail, Trash2, Shield, AlertCircle } from 'lucide-react';
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

const ROLE_LABELS: Record<string, { label: string; color: string; description: string }> = {
  owner: { label: 'Propietario', color: 'bg-purple-100 text-purple-800', description: 'Control total de la cuenta' },
  admin: { label: 'Administrador', color: 'bg-blue-100 text-blue-800', description: 'Gestión de equipo y configuración' },
  collaborator: { label: 'Colaborador', color: 'bg-green-100 text-green-800', description: 'Acceso de lectura/escritura completo' },
  viewer: { label: 'Visualizador', color: 'bg-gray-100 text-gray-800', description: 'Solo lectura' },
};

const TeamMembers: React.FC = () => {
  const user = useAuthStore((state) => state.user);
  const [isInviteDialogOpen, setIsInviteDialogOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteName, setInviteName] = useState('');
  const [inviteRole, setInviteRole] = useState('collaborator');
  const queryClient = useQueryClient();

  // Solo operadores pueden ver esta página
  if (user?.role === 'superadmin') {
    return (
      <div className="flex flex-col items-center justify-center h-screen">
        <AlertCircle className="w-12 h-12 text-yellow-500 mb-4" />
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Acceso Denegado</h1>
        <p className="text-gray-600">Los superadmins no pueden gestionar empleados aquí.</p>
        <p className="text-sm text-gray-500 mt-4">
          Esta página es solo para operadores de tenants.
        </p>
      </div>
    );
  }

  // Obtener listado de empleados
  const { data: teamData, isLoading } = useQuery<EmployeeListResponse>({
    queryKey: ['team', 'members'],
    queryFn: async () => {
      const response = await apiClient.get('/tenants/me/employees');
      return response.data;
    },
  });

  // Invitar empleado
  const inviteMutation = useMutation({
    mutationFn: async (data: { email: string; full_name: string; tenant_role: string }) => {
      const response = await apiClient.post('/tenants/me/employees', {
        email: data.email,
        full_name: data.full_name,
        tenant_role: data.tenant_role,
      });
      return response.data;
    },
    onSuccess: () => {
      toast.success('Empleado invitado exitosamente');
      setIsInviteDialogOpen(false);
      setInviteEmail('');
      setInviteName('');
      setInviteRole('collaborator');
      queryClient.invalidateQueries({ queryKey: ['team', 'members'] });
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Error al invitar empleado';
      toast.error(message);
    },
  });

  // Cambiar rol
  const changeRoleMutation = useMutation({
    mutationFn: async (data: { userId: string; role: string }) => {
      await apiClient.patch(`/tenants/me/employees/${data.userId}`, {
        tenant_role: data.role,
      });
    },
    onSuccess: () => {
      toast.success('Rol actualizado');
      queryClient.invalidateQueries({ queryKey: ['team', 'members'] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Error al cambiar rol');
    },
  });

  // Remover empleado
  const removeMutation = useMutation({
    mutationFn: async (userId: string) => {
      await apiClient.delete(`/tenants/me/employees/${userId}`);
    },
    onSuccess: () => {
      toast.success('Empleado removido');
      queryClient.invalidateQueries({ queryKey: ['team', 'members'] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Error al remover empleado');
    },
  });

  const handleInvite = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail) {
      toast.error('Por favor ingresa un email');
      return;
    }
    inviteMutation.mutate({
      email: inviteEmail,
      full_name: inviteName,
      tenant_role: inviteRole,
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Equipo de Trabajo</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Gestiona los miembros de tu equipo y asigna roles</p>
        </div>
        <Dialog open={isInviteDialogOpen} onOpenChange={setIsInviteDialogOpen}>
          <DialogTrigger asChild>
            <Button className="flex items-center gap-2">
              <UserPlus className="w-4 h-4" />
              Invitar Empleado
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Invitar Nuevo Empleado</DialogTitle>
              <DialogDescription>Añade un nuevo miembro a tu equipo de trabajo</DialogDescription>
            </DialogHeader>
            <form onSubmit={handleInvite} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="empleado@ejemplo.com"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="name">Nombre Completo (opcional)</Label>
                <Input
                  id="name"
                  type="text"
                  placeholder="Juan Pérez"
                  value={inviteName}
                  onChange={(e) => setInviteName(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="role">Rol</Label>
                <Select value={inviteRole} onValueChange={setInviteRole}>
                  <SelectTrigger id="role">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="viewer">
                      <div className="flex items-center gap-2">
                        <span>👁️ Visualizador</span>
                      </div>
                    </SelectItem>
                    <SelectItem value="collaborator">
                      <div className="flex items-center gap-2">
                        <span>✎ Colaborador</span>
                      </div>
                    </SelectItem>
                    <SelectItem value="admin">
                      <div className="flex items-center gap-2">
                        <span>⚙️ Administrador</span>
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-gray-500">
                  {inviteRole && ROLE_LABELS[inviteRole]?.description}
                </p>
              </div>

              <Button
                type="submit"
                disabled={inviteMutation.isPending || !inviteEmail}
                className="w-full"
              >
                {inviteMutation.isPending ? 'Enviando invitación...' : 'Enviar Invitación'}
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Estadísticas de roles */}
      {teamData && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(teamData.role_counts).map(([role, count]) => (
            <Card key={role} className="p-4">
              <div className="text-center">
                <p className="text-2xl font-bold">{count}</p>
                <p className="text-sm text-gray-600 dark:text-gray-400 capitalize">{ROLE_LABELS[role]?.label}</p>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Listado de miembros */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            Miembros del Equipo
          </CardTitle>
          <CardDescription>{teamData?.total_count || 0} miembro(s) total</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <p className="text-gray-500">Cargando miembros...</p>
            </div>
          ) : !teamData?.members || teamData.members.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Users className="w-12 h-12 text-gray-400 mb-4" />
              <p className="text-gray-600 dark:text-gray-400 mb-2">No hay miembros en el equipo</p>
              <p className="text-sm text-gray-500">Invita a empleados para comenzar a colaborar</p>
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
                              <Shield className="w-4 h-4" />
                              Propietario
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

export default TeamMembers;
