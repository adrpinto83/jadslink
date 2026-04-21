import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { toast } from "sonner";

interface Plan {
  id: string;
  name: string;
  duration_minutes: number;
  price_usd: string;
  is_active: boolean;
  created_at: string;
}

interface PlanForm {
  name: string;
  duration_minutes: number;
  price_usd: string;
}

const planTemplates: PlanForm[] = [
  { name: "30 Minutos", duration_minutes: 30, price_usd: "2.50" },
  { name: "1 Hora", duration_minutes: 60, price_usd: "4.00" },
  { name: "3 Horas", duration_minutes: 180, price_usd: "8.00" },
  { name: "Día (Bus)", duration_minutes: 480, price_usd: "12.00" },
  { name: "Día (Evento)", duration_minutes: 1440, price_usd: "20.00" },
  { name: "Semana", duration_minutes: 10080, price_usd: "50.00" },
];

const Plans: React.FC = () => {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [editingPlan, setEditingPlan] = useState<Plan | null>(null);
  const [formData, setFormData] = useState<PlanForm>({
    name: '',
    duration_minutes: 30,
    price_usd: '0.00',
  });

  const { data: plans, isLoading } = useQuery<Plan[]>({
    queryKey: ['plans'],
    queryFn: async () => {
      const response = await apiClient.get('/plans');
      return response.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (data: PlanForm) => {
      return await apiClient.post('/plans', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plans'] });
      resetForm();
      toast.success("Plan creado con éxito");
    },
    onError: () => {
      toast.error("Error al crear el plan");
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<PlanForm> }) => {
      return await apiClient.patch(`/plans/${id}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plans'] });
      resetForm();
      toast.success("Plan actualizado con éxito");
    },
    onError: () => {
      toast.error("Error al actualizar el plan");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      return await apiClient.delete(`/plans/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plans'] });
    },
    // We use toast.promise in handleDelete, so no need for explicit toasts here
  });

  const resetForm = () => {
    setFormData({ name: '', duration_minutes: 30, price_usd: '0.00' });
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
    });
    setShowForm(true);
  };

  const handleDelete = (id: string) => {
    toast.promise(deleteMutation.mutateAsync(id), {
      loading: 'Eliminando plan...',
      success: () => {
        // Invalidate queries is already handled by onSuccess in the mutation
        return 'Plan eliminado con éxito';
      },
      error: 'Error al eliminar el plan',
    });
  };
  
  const handleTemplateClick = (template: PlanForm) => {
    setEditingPlan(null); // Ensure we are in create mode
    setFormData(template);
    setShowForm(true);
  }

  const formatDuration = (minutes: number) => {
    if (minutes < 60) return `${minutes} min`;
    if (minutes < 1440) return `${minutes / 60} hr`;
    return `${minutes / 1440} día`;
  };

  if (isLoading) return <div>Cargando planes...</div>;

  return (
    <div className="space-y-6">
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
        </Card>
      )}

      {showForm && (
        <Card className="p-8 border-2 border-blue-200 bg-white">
          <h2 className="text-2xl font-bold mb-6">
            {editingPlan ? 'Editar Plan' : 'Crear Nuevo Plan'}
          </h2>
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
                {editingPlan ? 'Actualizar Plan' : 'Crear Plan'}
              </Button>
              <Button type="button" variant="outline" onClick={resetForm} className="flex-1">
                Cancelar
              </Button>
            </div>
          </form>
        </Card>
      )}

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
    </div>
  );
};

export default Plans;
