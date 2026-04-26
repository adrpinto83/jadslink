import React, { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuthStore } from '@/stores/auth';
import { AlertCircle, Check } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

interface PricingConfig {
  id: string;
  ticket_pack_size: number;
  ticket_pack_price_usd: string;
  additional_node_price_usd: string;
  free_plan_max_nodes: number;
  free_plan_max_tickets: number;
  basic_plan_max_nodes: number;
  basic_plan_max_free_tickets: number;
  description: string;
  created_at: string;
  updated_at: string;
}

const AdminPricing: React.FC = () => {
  const token = useAuthStore((state) => state.token);
  const [formData, setFormData] = useState<Partial<PricingConfig>>({});
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  // Fetch current pricing config
  const { data: pricingConfig, isLoading } = useQuery({
    queryKey: ['pricing-config'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE_URL}/admin/pricing`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return response.data as PricingConfig;
    },
    retry: 1,
  });

  // Initialize form with fetched data
  useEffect(() => {
    if (pricingConfig) {
      setFormData(pricingConfig);
    }
  }, [pricingConfig]);

  // Mutation for updating pricing
  const updatePricingMutation = useMutation({
    mutationFn: async (data: Partial<PricingConfig>) => {
      return await axios.patch(`${API_BASE_URL}/admin/pricing`, data, {
        headers: { Authorization: `Bearer ${token}` },
      });
    },
    onSuccess: (response) => {
      setFormData(response.data);
      setSuccessMessage('Configuración de precios actualizada exitosamente');
      setErrorMessage('');
      setTimeout(() => setSuccessMessage(''), 3000);
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Error al actualizar la configuración';
      setErrorMessage(message);
      setSuccessMessage('');
    },
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) : value,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updatePricingMutation.mutate(formData);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-500">Cargando configuración...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-3xl font-bold">Configuración de Precios</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Modifica los costos y límites de los planes
        </p>
      </div>

      {successMessage && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-600 dark:text-green-400 px-4 py-3 rounded-lg flex items-center gap-2">
          <Check className="w-5 h-5" />
          {successMessage}
        </div>
      )}

      {errorMessage && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 px-4 py-3 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          {errorMessage}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Tickets Section */}
        <Card>
          <CardHeader>
            <CardTitle>Configuración de Tickets</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="ticket_pack_size">Tamaño del Pack de Tickets</Label>
                <Input
                  id="ticket_pack_size"
                  name="ticket_pack_size"
                  type="number"
                  min="1"
                  value={formData.ticket_pack_size || ''}
                  onChange={handleInputChange}
                  placeholder="Ej: 50"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Cuántos tickets se venden en cada pack
                </p>
              </div>

              <div>
                <Label htmlFor="ticket_pack_price_usd">Precio del Pack (USD)</Label>
                <Input
                  id="ticket_pack_price_usd"
                  name="ticket_pack_price_usd"
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={formData.ticket_pack_price_usd || ''}
                  onChange={handleInputChange}
                  placeholder="Ej: 0.50"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Precio por cada pack
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Plan Free Limits */}
        <Card>
          <CardHeader>
            <CardTitle>Plan Free - Límites</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="free_plan_max_nodes">Máximo de Nodos</Label>
                <Input
                  id="free_plan_max_nodes"
                  name="free_plan_max_nodes"
                  type="number"
                  min="1"
                  value={formData.free_plan_max_nodes || ''}
                  onChange={handleInputChange}
                  placeholder="Ej: 1"
                />
              </div>

              <div>
                <Label htmlFor="free_plan_max_tickets">Máximo de Tickets Gratis</Label>
                <Input
                  id="free_plan_max_tickets"
                  name="free_plan_max_tickets"
                  type="number"
                  min="1"
                  value={formData.free_plan_max_tickets || ''}
                  onChange={handleInputChange}
                  placeholder="Ej: 50"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Plan Basic Limits */}
        <Card>
          <CardHeader>
            <CardTitle>Plan Básico - Límites</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="basic_plan_max_nodes">Máximo de Nodos</Label>
                <Input
                  id="basic_plan_max_nodes"
                  name="basic_plan_max_nodes"
                  type="number"
                  min="1"
                  value={formData.basic_plan_max_nodes || ''}
                  onChange={handleInputChange}
                  placeholder="Ej: 1"
                />
              </div>

              <div>
                <Label htmlFor="basic_plan_max_free_tickets">Máximo de Tickets Gratis Iniciales</Label>
                <Input
                  id="basic_plan_max_free_tickets"
                  name="basic_plan_max_free_tickets"
                  type="number"
                  min="1"
                  value={formData.basic_plan_max_free_tickets || ''}
                  onChange={handleInputChange}
                  placeholder="Ej: 50"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Additional Node Pricing */}
        <Card>
          <CardHeader>
            <CardTitle>Nodos Adicionales</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="additional_node_price_usd">Precio por Nodo Adicional (USD)</Label>
              <Input
                id="additional_node_price_usd"
                name="additional_node_price_usd"
                type="number"
                min="0.01"
                step="0.01"
                value={formData.additional_node_price_usd || ''}
                onChange={handleInputChange}
                placeholder="Ej: 50.00"
              />
              <p className="text-xs text-gray-500 mt-1">
                Costo para crear nodos adicionales en planes pagos
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Description */}
        <Card>
          <CardHeader>
            <CardTitle>Descripción</CardTitle>
          </CardHeader>
          <CardContent>
            <Input
              name="description"
              type="text"
              value={formData.description || ''}
              onChange={handleInputChange}
              placeholder="Ej: Configuración estándar de precios"
              maxLength={500}
            />
            <p className="text-xs text-gray-500 mt-1">
              {formData.description?.length || 0}/500 caracteres
            </p>
          </CardContent>
        </Card>

        {/* Submit Button */}
        <div className="flex gap-2">
          <Button
            type="submit"
            className="bg-blue-600 hover:bg-blue-700 text-white"
            disabled={updatePricingMutation.isPending}
          >
            {updatePricingMutation.isPending ? 'Guardando...' : 'Guardar Cambios'}
          </Button>
        </div>
      </form>

      {/* Current Configuration Summary */}
      {pricingConfig && (
        <Card className="bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
          <CardHeader>
            <CardTitle className="text-lg">Resumen Actual</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>
              <span className="font-semibold">Pack de Tickets:</span> {pricingConfig.ticket_pack_size} tickets = ${parseFloat(pricingConfig.ticket_pack_price_usd).toFixed(2)} USD
            </p>
            <p>
              <span className="font-semibold">Nodo Adicional:</span> ${parseFloat(pricingConfig.additional_node_price_usd).toFixed(2)} USD
            </p>
            <p>
              <span className="font-semibold">Plan Free:</span> Máx {pricingConfig.free_plan_max_nodes} nodo, {pricingConfig.free_plan_max_tickets} tickets gratis
            </p>
            <p>
              <span className="font-semibold">Plan Básico:</span> Máx {pricingConfig.basic_plan_max_nodes} nodo, {pricingConfig.basic_plan_max_free_tickets} tickets gratis
            </p>
            <p className="text-xs text-gray-600 dark:text-gray-400 pt-2">
              Última actualización: {new Date(pricingConfig.updated_at).toLocaleString('es-ES')}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AdminPricing;
