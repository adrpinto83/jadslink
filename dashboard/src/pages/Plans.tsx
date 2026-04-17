import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';

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
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<PlanForm> }) => {
      return await apiClient.patch(`/plans/${id}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plans'] });
      resetForm();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      return await apiClient.delete(`/plans/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plans'] });
    },
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
    if (confirm('¿Seguro que deseas eliminar este plan?')) {
      deleteMutation.mutate(id);
    }
  };

  const formatDuration = (minutes: number) => {
    if (minutes < 60) return `${minutes} min`;
    if (minutes < 1440) return `${minutes / 60} hr`;
    return `${minutes / 1440} día`;
  };

  if (isLoading) return <div>Cargando planes...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Planes de Tickets</h1>
        <Button onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancelar' : 'Nuevo Plan'}
        </Button>
      </div>

      {showForm && (
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">
            {editingPlan ? 'Editar Plan' : 'Crear Plan'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="name">Nombre del Plan</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="ej. 30 Minutos"
                required
              />
            </div>
            <div>
              <Label htmlFor="duration">Duración (minutos)</Label>
              <Input
                id="duration"
                type="number"
                value={formData.duration_minutes}
                onChange={(e) =>
                  setFormData({ ...formData, duration_minutes: parseInt(e.target.value) })
                }
                min="1"
                required
              />
            </div>
            <div>
              <Label htmlFor="price">Precio (USD)</Label>
              <Input
                id="price"
                type="number"
                step="0.01"
                value={formData.price_usd}
                onChange={(e) => setFormData({ ...formData, price_usd: e.target.value })}
                min="0"
                required
              />
            </div>
            <div className="flex gap-2">
              <Button type="submit" disabled={createMutation.isPending || updateMutation.isPending}>
                {editingPlan ? 'Actualizar' : 'Crear'}
              </Button>
              <Button type="button" variant="outline" onClick={resetForm}>
                Cancelar
              </Button>
            </div>
          </form>
        </Card>
      )}

      <Card className="p-6">
        <Table>
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Duración</th>
              <th>Precio</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {plans?.map((plan) => (
              <tr key={plan.id}>
                <td className="font-medium">{plan.name}</td>
                <td>{formatDuration(plan.duration_minutes)}</td>
                <td>${plan.price_usd}</td>
                <td>
                  <Badge variant={plan.is_active ? 'default' : 'secondary'}>
                    {plan.is_active ? 'Activo' : 'Inactivo'}
                  </Badge>
                </td>
                <td>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => handleEdit(plan)}>
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
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
        {!plans?.length && (
          <p className="text-center py-8 text-gray-500">No hay planes creados</p>
        )}
      </Card>
    </div>
  );
};

export default Plans;
