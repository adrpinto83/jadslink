/**
 * Component showing JADSlink banking data for Pago Móvil transfers
 */

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Copy, Check, CreditCard } from 'lucide-react';
import { useState } from 'react';

export const DatosBancariosJADS: React.FC = () => {
  const [copiedField, setCopiedField] = useState<string | null>(null);

  const bankingData = {
    cedula: 'V-16140066',
    telefonoPagoMovil: '0424-8886222',
    bancos: ['Bancamiga', 'Mercantil', 'Venezuela'],
  };

  const handleCopy = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);

    // Reset after 2 seconds
    setTimeout(() => setCopiedField(null), 2000);
  };

  return (
    <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/30 border-blue-200 dark:border-blue-800">
      <CardHeader>
        <div className="flex items-center gap-2">
          <CreditCard className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          <div>
            <CardTitle className="text-blue-900 dark:text-blue-100">
              Datos para Transferir (JADSlink)
            </CardTitle>
            <CardDescription className="text-blue-700 dark:text-blue-300">
              Utiliza estos datos para realizar tu transferencia bancaria
            </CardDescription>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Cédula */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Cédula / RIF del Beneficiario
          </label>
          <div className="flex items-center justify-between bg-white dark:bg-gray-800 p-3 rounded-lg border border-blue-200 dark:border-blue-700">
            <code className="text-lg font-mono font-bold text-blue-600 dark:text-blue-400">
              {bankingData.cedula}
            </code>
            <button
              onClick={() => handleCopy(bankingData.cedula, 'cedula')}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
              title="Copiar"
            >
              {copiedField === 'cedula' ? (
                <Check className="w-4 h-4 text-green-600" />
              ) : (
                <Copy className="w-4 h-4 text-gray-500" />
              )}
            </button>
          </div>
        </div>

        {/* Teléfono Pago Móvil */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Teléfono Pago Móvil
          </label>
          <div className="flex items-center justify-between bg-white dark:bg-gray-800 p-3 rounded-lg border border-blue-200 dark:border-blue-700">
            <code className="text-lg font-mono font-bold text-blue-600 dark:text-blue-400">
              {bankingData.telefonoPagoMovil}
            </code>
            <button
              onClick={() => handleCopy(bankingData.telefonoPagoMovil, 'telefono')}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
              title="Copiar"
            >
              {copiedField === 'telefono' ? (
                <Check className="w-4 h-4 text-green-600" />
              ) : (
                <Copy className="w-4 h-4 text-gray-500" />
              )}
            </button>
          </div>
        </div>

        {/* Bancos */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Bancos Aceptados
          </label>
          <div className="flex flex-wrap gap-2">
            {bankingData.bancos.map((banco) => (
              <Badge key={banco} variant="secondary" className="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-100">
                {banco}
              </Badge>
            ))}
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-6 pt-4 border-t border-blue-200 dark:border-blue-700">
          <p className="text-sm text-blue-800 dark:text-blue-200">
            <strong>📱 Cómo transferir:</strong>
          </p>
          <ol className="text-xs text-blue-700 dark:text-blue-300 list-decimal list-inside mt-2 space-y-1">
            <li>Abre tu app bancaria y selecciona "Pago Móvil"</li>
            <li>Selecciona uno de los bancos listados arriba</li>
            <li>Ingresa la cédula V-16140066</li>
            <li>Ingresa el teléfono 0424-8886222</li>
            <li>Ingresa el monto en VEF (convertido según la tasa)</li>
            <li>Completa la transacción y guarda la referencia</li>
            <li>Copia la referencia en el formulario abajo</li>
          </ol>
        </div>
      </CardContent>
    </Card>
  );
};
