import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/api/client';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';

interface Tenant {
  id: string;
  name: string;
  slug: string;
  plan_tier: string;
  is_active: boolean;
  created_at: string;
  settings: {
    logo_url?: string;
    primary_color?: string;
    custom_domain?: string;
  } | null;
}

interface SettingsForm {
  logo_url: string;
  primary_color: string;
  custom_domain: string;
}

const Settings: React.FC = () => {
  const queryClient = useQueryClient();
  const [hasChanges, setHasChanges] = useState(false);

  const { data: tenant, isLoading } = useQuery<Tenant>({
    queryKey: ['tenant', 'me'],
    queryFn: async () => {
      const response = await apiClient.get('/tenants/me');
      return response.data;
    },
  });

  const [formData, setFormData] = useState<SettingsForm>({
    logo_url: tenant?.settings?.logo_url || '',
    primary_color: tenant?.settings?.primary_color || '#3b82f6',
    custom_domain: tenant?.settings?.custom_domain || '',
  });

  React.useEffect(() => {
    if (tenant?.settings) {
      setFormData({
        logo_url: tenant.settings.logo_url || '',
        primary_color: tenant.settings.primary_color || '#3b82f6',
        custom_domain: tenant.settings.custom_domain || '',
      });
    }
  }, [tenant]);

  const updateMutation = useMutation({
    mutationFn: async (data: Partial<SettingsForm>) => {
      return await apiClient.patch('/tenants/me', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenant', 'me'] });
      setHasChanges(false);
    },
  });

  const handleInputChange = (field: keyof SettingsForm, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setHasChanges(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const updates: Partial<SettingsForm> = {};

    if (formData.logo_url !== tenant?.settings?.logo_url) {
      updates.logo_url = formData.logo_url;
    }
    if (formData.primary_color !== tenant?.settings?.primary_color) {
      updates.primary_color = formData.primary_color;
    }
    if (formData.custom_domain !== tenant?.settings?.custom_domain) {
      updates.custom_domain = formData.custom_domain;
    }

    if (Object.keys(updates).length > 0) {
      updateMutation.mutate(updates);
    }
  };

  const handleReset = () => {
    setFormData({
      logo_url: tenant?.settings?.logo_url || '',
      primary_color: tenant?.settings?.primary_color || '#3b82f6',
      custom_domain: tenant?.settings?.custom_domain || '',
    });
    setHasChanges(false);
  };

  if (isLoading) return <div>Cargando configuración...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Configuración</h1>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Información de la Cuenta</h2>
          <div className="space-y-3">
            <div>
              <Label className="text-sm text-gray-600 dark:text-gray-400">Empresa</Label>
              <p className="font-medium">{tenant?.name}</p>
            </div>
            <div>
              <Label className="text-sm text-gray-600 dark:text-gray-400">Slug</Label>
              <p className="font-mono text-sm">{tenant?.slug}</p>
            </div>
            <div>
              <Label className="text-sm text-gray-600 dark:text-gray-400">Plan</Label>
              <div className="mt-1">
                <Badge variant="default">{tenant?.plan_tier}</Badge>
              </div>
            </div>
            <div>
              <Label className="text-sm text-gray-600 dark:text-gray-400">Estado</Label>
              <div className="mt-1">
                <Badge variant={tenant?.is_active ? 'default' : 'secondary'}>
                  {tenant?.is_active ? 'Activo' : 'Inactivo'}
                </Badge>
              </div>
            </div>
            <div>
              <Label className="text-sm text-gray-600 dark:text-gray-400">Creado</Label>
              <p className="text-sm">
                {tenant?.created_at
                  ? new Date(tenant.created_at).toLocaleDateString('es-ES', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                    })
                  : 'N/A'}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Personalización</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="logo_url">URL del Logo</Label>
              <Input
                id="logo_url"
                type="url"
                value={formData.logo_url}
                onChange={(e) => handleInputChange('logo_url', e.target.value)}
                placeholder="https://ejemplo.com/logo.png"
              />
              <p className="text-xs text-gray-500 mt-1">
                Se mostrará en el portal de tickets
              </p>
            </div>

            <div>
              <Label htmlFor="primary_color">Color Primario</Label>
              <div className="flex gap-2">
                <Input
                  id="primary_color"
                  type="color"
                  value={formData.primary_color}
                  onChange={(e) => handleInputChange('primary_color', e.target.value)}
                  className="w-20 h-10"
                />
                <Input
                  type="text"
                  value={formData.primary_color}
                  onChange={(e) => handleInputChange('primary_color', e.target.value)}
                  placeholder="#3b82f6"
                  pattern="^#[0-9A-Fa-f]{6}$"
                  className="flex-1"
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Personaliza el color de tu portal
              </p>
            </div>

            <div>
              <Label htmlFor="custom_domain">Dominio Personalizado</Label>
              <Input
                id="custom_domain"
                type="text"
                value={formData.custom_domain}
                onChange={(e) => handleInputChange('custom_domain', e.target.value)}
                placeholder="portal.miempresa.com"
              />
              <p className="text-xs text-gray-500 mt-1">
                Disponible en planes Pro y Enterprise
              </p>
            </div>

            <div className="flex gap-2 pt-2">
              <Button
                type="submit"
                disabled={!hasChanges || updateMutation.isPending}
              >
                {updateMutation.isPending ? 'Guardando...' : 'Guardar Cambios'}
              </Button>
              {hasChanges && (
                <Button type="button" variant="outline" onClick={handleReset}>
                  Cancelar
                </Button>
              )}
            </div>

            {updateMutation.isSuccess && (
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-600 dark:text-green-400 px-4 py-3 rounded">
                Configuración actualizada correctamente
              </div>
            )}

            {updateMutation.isError && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 px-4 py-3 rounded">
                Error al actualizar la configuración
              </div>
            )}
          </form>
        </Card>
      </div>
    </div>
  );
};

export default Settings;
