import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Plus, Search, Wifi, ArrowDown, ArrowUp, Users, CheckCircle, XCircle } from 'lucide-react';

interface Plan {
  id: string;
  name: string;
  duration_minutes: number;
  price_usd: string;
  bandwidth_down_kbps: number;
  bandwidth_up_kbps: number;
  max_devices: number;
  is_active: boolean;
  created_at: string;
}

interface PlanForm {
  name: string;
  duration_minutes: number;
  price_usd: string;
  bandwidth_down_kbps: number;
  bandwidth_up_kbps: number;
  max_devices: number;
  is_active: boolean;
}

const planTemplates: Omit<PlanForm, 'is_active'>[] = [
  { name: "30 Minutos", duration_minutes: 30, price_usd: "2.50", bandwidth_down_kbps: 5000, bandwidth_up_kbps: 1000, max_devices: 1 },
  { name: "1 Hora", duration_minutes: 60, price_usd: "4.00", bandwidth_down_kbps: 5000, bandwidth_up_kbps: 1000, max_devices: 1 },
  { name: "Día Completo", duration_minutes: 1440, price_usd: "10.00", bandwidth_down_kbps: 10000, bandwidth_up_kbps: 2000, max_devices: 2 },
];

const StatCard = ({ title, value, icon: Icon }: { title: string; value: number; icon: React.ElementType }) => (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
      </CardContent>
    </Card>
  );

const Plans: React.FC = () => {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [editingPlan, setEditingPlan] = useState<Plan | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState<PlanForm>({
    name: '',
    duration_minutes: 30,
    price_usd: '0.00',
    bandwidth_down_kbps: 0,
    bandwidth_up_kbps: 0,
    max_devices: 1,
    is_active: true,
  });

  const { data: plans = [], isLoading } = useQuery<Plan[]>({
    queryKey: ['plans'],
    queryFn: async () => apiClient.get('/plans').then(res => res.data),
  });

  const createMutation = useMutation({
    mutationFn: (data: PlanForm) => apiClient.post('/plans', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plans'] });
      resetForm();
      toast.success("Plan creado con éxito");
    },
    onError: () => toast.error("Error al crear el plan"),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<PlanForm> }) => apiClient.patch(`/plans/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plans'] });
      resetForm();
      toast.success("Plan actualizado con éxito");
    },
    onError: () => toast.error("Error al actualizar el plan"),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/plans/${id}`),
    onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['plans'] });
        toast.success('Plan eliminado con éxito');
    },
    onError: () => toast.error("Error al eliminar el plan"),
  });

  const resetForm = () => {
    setFormData({ name: '', duration_minutes: 30, price_usd: '0.00', bandwidth_down_kbps: 0, bandwidth_up_kbps: 0, max_devices: 1, is_active: true });
    setShowForm(false);
    setEditingPlan(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editingPlan) {
      updateMutation.mutate({ id: editingPlan.id, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleEdit = (plan: Plan) => {
    setEditingPlan(plan);
    setFormData({
      name: plan.name,
      duration_minutes: plan.duration_minutes,
      price_usd: plan.price_usd,
      bandwidth_down_kbps: plan.bandwidth_down_kbps,
      bandwidth_up_kbps: plan.bandwidth_up_kbps,
      max_devices: plan.max_devices,
      is_active: plan.is_active,
    });
    setShowForm(true);
  };

  const handleDelete = (id: string) => {
    if (window.confirm('¿Estás seguro de que quieres eliminar este plan?')) {
        deleteMutation.mutate(id);
    }
  };
  
  const handleTemplateClick = (template: Omit<PlanForm, 'is_active'>) => {
    setEditingPlan(null);
    setFormData({ ...template, is_active: true });
    setShowForm(true);
  }

  const formatDuration = (minutes: number) => {
    if (minutes < 60) return `${minutes} min`;
    if (minutes < 1440) return `${Math.floor(minutes / 60)}h ${minutes % 60}m`;
    return `${Math.floor(minutes / 1440)}d ${Math.floor((minutes % 1440) / 60)}h`;
  };

  const filteredPlans = plans.filter(plan => 
    plan.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const activePlans = plans.filter(p => p.is_active).length;

  if (isLoading) return <div>Cargando planes...</div>;

  return (
    <div className="space-y-6">
<<<<<<< HEAD
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Planes de Tickets</h1>
          <p className="text-gray-600 mt-1">Crea y administra planes personalizados con precios propios</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancelar' : '+ Nuevo Plan'}
        </Button>
      </div>

      {/* Create Form or Templates */}
      {!showForm && plans && plans.length === 0 && (
        <Card className="p-6 border-2 border-dashed border-blue-200 bg-blue-50">
          <div className="text-center space-y-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Sin planes aún</h3>
              <p className="text-gray-600">Crea tu primer plan o usa una plantilla como base</p>
            </div>
            <div className="flex flex-wrap gap-2 justify-center">
              <Button onClick={() => setShowForm(true)} variant="default">
                Crear Plan Personalizado
              </Button>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-3">O usa una plantilla:</p>
              <div className="flex flex-wrap gap-2 justify-center">
                {planTemplates.map(template => (
                  <Button key={template.name} variant="outline" size="sm" onClick={() => handleTemplateClick(template)}>
                    {template.name}
                  </Button>
                ))}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Plan Templates (shown when user has plans) */}
      {!showForm && plans && plans.length > 0 && (
        <Card className="p-4 bg-gray-50">
          <h3 className="text-sm font-semibold mb-3 text-gray-700">Crear desde plantilla:</h3>
          <div className="flex flex-wrap gap-2">
            {planTemplates.map(template => (
              <Button key={template.name} variant="outline" size="sm" onClick={() => handleTemplateClick(template)}>
                {template.name}
              </Button>
            ))}
          </div>
=======
        <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold">Planes de Tickets</h1>
            <Button onClick={() => { setShowForm(!showForm); setEditingPlan(null); }}>
            <Plus className="mr-2 h-4 w-4" /> {showForm ? 'Cancelar' : 'Nuevo Plan'}
            </Button>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
            <StatCard title="Planes Totales" value={plans.length} icon={Wifi} />
            <StatCard title="Planes Activos" value={activePlans} icon={CheckCircle} />
            <StatCard title="Planes Inactivos" value={plans.length - activePlans} icon={XCircle} />
        </div>

      {/* Plan Templates */}
      {!showForm && (
        <Card>
            <CardHeader>
                <CardTitle>Plantillas</CardTitle>
                <CardDescription>Crea planes rápidamente usando plantillas predefinidas.</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
                {planTemplates.map(template => (
                    <Button key={template.name} variant="outline" size="sm" onClick={() => handleTemplateClick(template)}>
                        {template.name}
                    </Button>
                ))}
            </CardContent>
>>>>>>> 77eed95 (Refactorización de la lógica de planes y actualización del dashboard)
        </Card>
      )}

      {showForm && (
        <Card className="p-8 border-2 border-blue-200 bg-white">
          <h2 className="text-2xl font-bold mb-6">
            {editingPlan ? 'Editar Plan' : 'Crear Nuevo Plan'}
          </h2>
<<<<<<< HEAD
          <form onSubmit={handleSubmit} className="space-y-6 max-w-md">
            <div className="space-y-2">
              <Label htmlFor="name" className="text-sm font-medium">Nombre del Plan</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="ej. 30 Minutos, Acceso Diario, etc."
                required
                className="border border-gray-300"
              />
              <p className="text-xs text-gray-500">Nombre visible para tus clientes</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="duration" className="text-sm font-medium">Duración (minutos)</Label>
              <Input
                id="duration"
                type="number"
                value={formData.duration_minutes}
                onChange={(e) =>
                  setFormData({ ...formData, duration_minutes: parseInt(e.target.value) })
                }
                min="1"
                required
                className="border border-gray-300"
              />
              <p className="text-xs text-gray-500">ej. 30, 60, 1440 (1 día)</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="price" className="text-sm font-medium">Precio (USD)</Label>
              <div className="flex items-center gap-2">
                <span className="text-gray-500">$</span>
                <Input
                  id="price"
                  type="number"
                  step="0.01"
                  value={formData.price_usd}
                  onChange={(e) => setFormData({ ...formData, price_usd: e.target.value })}
                  min="0"
                  required
                  placeholder="0.00"
                  className="border border-gray-300"
                />
              </div>
              <p className="text-xs text-gray-500">Define el precio que quieres cobrar</p>
            </div>

            <div className="bg-blue-50 p-3 rounded-lg border border-blue-100">
              <p className="text-sm font-medium text-blue-900">Vista previa:</p>
              <p className="text-sm text-blue-700 mt-1">
                {formData.name || 'Plan'} - {formData.duration_minutes || 0} min - ${formData.price_usd || '0.00'}
              </p>
            </div>

            <div className="flex gap-2 pt-4">
              <Button type="submit" disabled={createMutation.isPending || updateMutation.isPending} className="flex-1">
=======
          <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label htmlFor="name">Nombre del Plan</Label>
              <Input id="name" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} placeholder="ej. 30 Minutos" required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="duration">Duración (minutos)</Label>
              <Input id="duration" type="number" value={formData.duration_minutes} onChange={(e) => setFormData({ ...formData, duration_minutes: parseInt(e.target.value) })} min="1" required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="price">Precio (USD)</Label>
              <Input id="price" type="number" step="0.01" value={formData.price_usd} onChange={(e) => setFormData({ ...formData, price_usd: e.target.value })} min="0" required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="max_devices">Máx. Dispositivos</Label>
              <Input id="max_devices" type="number" value={formData.max_devices} onChange={(e) => setFormData({ ...formData, max_devices: parseInt(e.target.value) })} min="1" required />
            </div>
            <div className="space-y-2">
                <Label htmlFor="bw_down">Velocidad de Bajada (Kbps)</Label>
                <Input id="bw_down" type="number" value={formData.bandwidth_down_kbps} onChange={(e) => setFormData({...formData, bandwidth_down_kbps: parseInt(e.target.value)})} min="0" />
                <p className="text-xs text-muted-foreground">0 para ilimitado.</p>
            </div>
            <div className="space-y-2">
                <Label htmlFor="bw_up">Velocidad de Subida (Kbps)</Label>
                <Input id="bw_up" type="number" value={formData.bandwidth_up_kbps} onChange={(e) => setFormData({...formData, bandwidth_up_kbps: parseInt(e.target.value)})} min="0" />
                <p className="text-xs text-muted-foreground">0 para ilimitado.</p>
            </div>
            <div className="flex items-center space-x-2 md:col-span-2">
                <input type="checkbox" id="is_active" checked={formData.is_active} onChange={(e) => setFormData({...formData, is_active: e.target.checked})} />
                <Label htmlFor="is_active">Plan Activo</Label>
            </div>
            <div className="flex gap-2 md:col-span-2">
              <Button type="submit" disabled={createMutation.isPending || updateMutation.isPending}>
>>>>>>> 77eed95 (Refactorización de la lógica de planes y actualización del dashboard)
                {editingPlan ? 'Actualizar Plan' : 'Crear Plan'}
              </Button>
              <Button type="button" variant="outline" onClick={resetForm} className="flex-1">
                Cancelar
              </Button>
            </div>
          </form>
        </Card>
      )}

<<<<<<< HEAD
      {plans && plans.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Tus Planes Activos</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {plans.map((plan) => (
              <div key={plan.id} className="border border-gray-200 rounded-lg p-4 bg-gradient-to-br from-white to-gray-50 hover:shadow-md transition-shadow">
                <div className="space-y-3">
                  <div>
                    <h4 className="text-lg font-semibold text-gray-900">{plan.name}</h4>
                    <p className="text-sm text-gray-500 mt-1">
                      {formatDuration(plan.duration_minutes)} de acceso
                    </p>
                  </div>

                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-bold text-blue-600">${plan.price_usd}</span>
                    <span className="text-sm text-gray-500">USD</span>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-gray-200">
                    <Badge variant={plan.is_active ? 'default' : 'secondary'}>
                      {plan.is_active ? 'Activo' : 'Inactivo'}
                    </Badge>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleEdit(plan)}
                      >
                        Editar
                      </Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => handleDelete(plan.id)}
                        disabled={deleteMutation.isPending}
                      >
                        Eliminar
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
=======
      <Card>
        <CardHeader>
            <CardTitle>Todos los Planes</CardTitle>
            <div className="mt-4 relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input placeholder="Buscar por nombre..." className="pl-8 w-full" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} />
            </div>
        </CardHeader>
        <CardContent>
            <Table>
            <TableHeader>
                <TableRow>
                <TableHead>Nombre</TableHead>
                <TableHead>Duración</TableHead>
                <TableHead>Precio</TableHead>
                <TableHead><div className="flex items-center"><ArrowDown className="h-4 w-4 mr-1" /> (Kbps)</div></TableHead>
                <TableHead><div className="flex items-center"><ArrowUp className="h-4 w-4 mr-1" /> (Kbps)</div></TableHead>
                <TableHead><div className="flex items-center"><Users className="h-4 w-4 mr-1" /></div></TableHead>
                <TableHead>Estado</TableHead>
                <TableHead className="text-right">Acciones</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {filteredPlans.map((plan) => (
                <TableRow key={plan.id}>
                    <TableCell className="font-medium">{plan.name}</TableCell>
                    <TableCell>{formatDuration(plan.duration_minutes)}</TableCell>
                    <TableCell>${plan.price_usd}</TableCell>
                    <TableCell>{plan.bandwidth_down_kbps === 0 ? 'Ilimitado' : plan.bandwidth_down_kbps}</TableCell>
                    <TableCell>{plan.bandwidth_up_kbps === 0 ? 'Ilimitado' : plan.bandwidth_up_kbps}</TableCell>
                    <TableCell>{plan.max_devices}</TableCell>
                    <TableCell>
                        <Badge variant={plan.is_active ? 'default' : 'secondary'}>
                            {plan.is_active ? 'Activo' : 'Inactivo'}
                        </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                        <Button size="sm" variant="outline" onClick={() => handleEdit(plan)} className="mr-2">Editar</Button>
                        <Button size="sm" variant="destructive" onClick={() => handleDelete(plan.id)} disabled={deleteMutation.isPending}>
                            Eliminar
                        </Button>
                    </TableCell>
                </TableRow>
                ))}
            </TableBody>
            </Table>
            {!filteredPlans.length && (
            <p className="text-center py-8 text-gray-500">No se encontraron planes.</p>
            )}
        </CardContent>
      </Card>
>>>>>>> 77eed95 (Refactorización de la lógica de planes y actualización del dashboard)
    </div>
  );
};

export default Plans;
