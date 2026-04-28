import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, CheckCircle2 } from 'lucide-react';
import { DatosBancariosJADS } from '@/components/DatosBancariosJADS';
import { FileUpload } from '@/components/FileUpload';
import { validateCedula, validateReferencia, BANCOS_VENEZUELA } from '@/utils/validators';

interface PagoMovilFormProps {
  onSubmit: (data: {
    banco_origen: string;
    cédula_pagador: string;
    referencia_pago: string;
    comprobante_url: string;
  }) => void;
  isLoading?: boolean;
  exchangeRate?: number;
  amountUsd?: number;
}

export const PagoMovilForm: React.FC<PagoMovilFormProps> = ({
  onSubmit,
  isLoading = false,
  exchangeRate = 36.50,
  amountUsd = 0.50,
}) => {
  const [banco, setBanco] = useState('');
  const [cedula, setCedula] = useState('');
  const [referencia, setReferencia] = useState('');
  const [comprobante, setComprobante] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const amountVef = amountUsd * exchangeRate;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: Record<string, string> = {};

    // Validate banco
    if (!banco) {
      newErrors.banco = 'Selecciona un banco';
    }

    // Validate cédula
    if (!cedula) {
      newErrors.cedula = 'Cédula es requerida';
    } else {
      const result = validateCedula(cedula);
      if (!result.isValid) {
        newErrors.cedula = result.error || 'Cédula inválida';
      }
    }

    // Validate referencia
    if (!referencia) {
      newErrors.referencia = 'Referencia es requerida';
    } else {
      const result = validateReferencia(referencia);
      if (!result.isValid) {
        newErrors.referencia = result.error || 'Referencia inválida';
      }
    }

    // Validate comprobante - must be a valid URL (absolute or relative) or non-empty string
    if (!comprobante) {
      newErrors.comprobante = 'Comprobante es requerido';
    } else if (!comprobante.startsWith('http') && !comprobante.startsWith('/')) {
      newErrors.comprobante = 'Comprobante debe tener una URL válida';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    // Normalize values before submission
    const cedulaResult = validateCedula(cedula);
    const referenciaResult = validateReferencia(referencia);

    onSubmit({
      banco_origen: banco,
      cédula_pagador: cedulaResult.normalized || cedula,
      referencia_pago: referenciaResult.normalized || referencia,
      comprobante_url: comprobante,
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Detalles de Pago Móvil</CardTitle>
        <CardDescription>
          Completa los datos de tu transferencia bancaria
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* DATOS BANCARIOS DE JADSLINK */}
          <div className="mb-6">
            <DatosBancariosJADS />
          </div>

          {/* MONTO A TRANSFERIR */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950 dark:to-indigo-950 p-4 rounded-lg">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Monto en USD</p>
                <p className="text-2xl font-bold text-blue-600">${amountUsd.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Monto en VEF (Tasa oficial)</p>
                <p className="text-2xl font-bold text-blue-600">Bs. {amountVef.toFixed(2)}</p>
                <p className="text-xs text-gray-500 mt-1">Tasa: 1 USD = {exchangeRate} VEF</p>
              </div>
            </div>
          </div>

          {/* INSTRUCCIONES */}
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <p className="font-semibold mb-1">📱 Instrucciones:</p>
              <ol className="text-sm space-y-1 ml-4 list-decimal">
                <li>Abre tu app bancaria</li>
                <li>Selecciona "Pago Móvil" o "Transferencia"</li>
                <li>Ingresa el banco de JADSlink y cédula</li>
                <li>Copia la referencia que se genera</li>
                <li>Toma screenshot del comprobante</li>
                <li>Sube el comprobante con URL válida</li>
              </ol>
            </AlertDescription>
          </Alert>

          {/* BANCO */}
          <div className="space-y-2">
            <Label htmlFor="banco">Tu Banco Origen (donde tienes dinero)</Label>
            <Select value={banco} onValueChange={setBanco}>
              <SelectTrigger id="banco" className={errors.banco ? 'border-red-500' : ''}>
                <SelectValue placeholder="Selecciona tu banco..." />
              </SelectTrigger>
              <SelectContent>
                {BANCOS_VENEZUELA.map((bancName) => (
                  <SelectItem key={bancName} value={bancName}>
                    {bancName}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.banco && <p className="text-sm text-red-500">{errors.banco}</p>}
            <p className="text-xs text-gray-500">
              Selecciona el banco desde donde realizarás la transferencia
            </p>
          </div>

          {/* CÉDULA */}
          <div className="space-y-2">
            <Label htmlFor="cedula">Tu Cédula (del que pagador)</Label>
            <Input
              id="cedula"
              type="text"
              placeholder="Ej: V-12345678 o 12345678"
              value={cedula}
              onChange={(e) => setCedula(e.target.value.toUpperCase())}
              onBlur={() => {
                if (cedula) {
                  const result = validateCedula(cedula);
                  if (result.isValid && result.normalized) {
                    setCedula(result.normalized);
                  }
                }
              }}
              className={`${errors.cedula ? 'border-red-500' : ''}`}
            />
            {errors.cedula && <p className="text-sm text-red-500">{errors.cedula}</p>}
            {cedula && !errors.cedula && (
              <div className="flex items-center gap-2 text-sm text-green-600">
                <CheckCircle2 className="w-4 h-4" />
                Formato válido
              </div>
            )}
            <p className="text-xs text-gray-500">Formato: V-12345678 o E-12345678</p>
          </div>

          {/* REFERENCIA */}
          <div className="space-y-2">
            <Label htmlFor="referencia">Referencia de Pago (8-12 dígitos)</Label>
            <Input
              id="referencia"
              type="text"
              placeholder="Ej: 1234567890"
              value={referencia}
              onChange={(e) => setReferencia(e.target.value.replace(/\D/g, ''))}
              maxLength={12}
              className={`${errors.referencia ? 'border-red-500' : ''}`}
            />
            {errors.referencia && <p className="text-sm text-red-500">{errors.referencia}</p>}
            {referencia && !errors.referencia && (
              <div className="flex items-center gap-2 text-sm text-green-600">
                <CheckCircle2 className="w-4 h-4" />
                Referencia válida ({referencia.length} dígitos)
              </div>
            )}
            <p className="text-xs text-gray-500">
              La referencia que genera tu banco al confirmar la transferencia Pago Móvil
            </p>
          </div>

          {/* COMPROBANTE UPLOAD */}
          <div className="space-y-2">
            <Label htmlFor="comprobante">Comprobante de Pago</Label>
            <FileUpload
              onUploadComplete={(url) => setComprobante(url)}
              maxSizeMB={5}
              acceptedFormats={['image/png', 'image/jpeg', 'application/pdf']}
            />
            {errors.comprobante && <p className="text-sm text-red-500">{errors.comprobante}</p>}
            <p className="text-xs text-gray-500">
              Sube el screenshot o PDF del comprobante bancario. Máximo 5MB.
            </p>
          </div>

          {/* BOTÓN ENVIAR */}
          <Button
            type="submit"
            disabled={isLoading || !banco || !cedula || !referencia || !comprobante}
            className="w-full h-10 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
          >
            {isLoading ? 'Procesando...' : 'Solicitar Pago'}
          </Button>

          {/* AVISO */}
          <Alert className="bg-yellow-50 dark:bg-yellow-950 border-yellow-200 dark:border-yellow-800">
            <AlertCircle className="h-4 w-4 text-yellow-600" />
            <AlertDescription className="text-sm text-yellow-800 dark:text-yellow-200">
              ⏳ Tu solicitud será revisada en 24-48 horas. Te enviaremos email cuando sea confirmada.
            </AlertDescription>
          </Alert>
        </form>
      </CardContent>
    </Card>
  );
};
