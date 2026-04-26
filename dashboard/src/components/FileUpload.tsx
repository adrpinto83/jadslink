/**
 * File upload component with drag & drop support
 */

import React, { useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { FileUp, X, CheckCircle } from 'lucide-react';
import apiClient from '@/api/client';
import { toast } from 'sonner';

interface FileUploadProps {
  onUploadComplete: (url: string) => void;
  maxSizeMB?: number;
  acceptedFormats?: string[];
}

export const FileUpload: React.FC<FileUploadProps> = ({
  onUploadComplete,
  maxSizeMB = 5,
  acceptedFormats = ['image/png', 'image/jpeg', 'application/pdf'],
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<{ name: string; url: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    // Check file type
    if (!acceptedFormats.includes(file.type)) {
      return 'Formato no permitido. Usa PNG, JPG o PDF.';
    }

    // Check file size
    if (file.size > maxSizeMB * 1024 * 1024) {
      return `Archivo muy grande. Máximo ${maxSizeMB}MB.`;
    }

    return null;
  };

  const handleUpload = async (file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      setUploadedFile(null);
      return;
    }

    setError(null);
    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await apiClient.post('/uploads/comprobante', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.success && response.data.url) {
        setUploadedFile({
          name: file.name,
          url: response.data.url,
        });
        onUploadComplete(response.data.url);
        toast.success('Comprobante subido exitosamente');
      } else {
        throw new Error(response.data.message || 'Error desconocido');
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al subir archivo';
      setError(errorMsg);
      setUploadedFile(null);
      toast.error(errorMsg);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file) {
      handleUpload(file);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleUpload(file);
    }
  };

  const handleRemove = () => {
    setUploadedFile(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="space-y-3">
      {!uploadedFile ? (
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer ${
            isDragging
              ? 'border-blue-500 bg-blue-50 dark:bg-blue-950'
              : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
          }`}
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <FileUp className="w-12 h-12 mx-auto text-gray-400 mb-3" />
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2 font-medium">
            Arrastra tu comprobante aquí o haz clic para seleccionar
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept={acceptedFormats.join(',')}
            onChange={handleFileSelect}
            className="hidden"
            disabled={isUploading}
          />
          <p className="text-xs text-gray-500 mt-2">
            PNG, JPG, PDF • Máx {maxSizeMB}MB
          </p>

          {isUploading && (
            <div className="mt-3">
              <div className="inline-flex items-center gap-2 text-sm text-blue-600">
                <div className="animate-spin">
                  <FileUp className="w-4 h-4" />
                </div>
                Subiendo archivo...
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="border border-green-200 bg-green-50 dark:bg-green-950/20 dark:border-green-800 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
              <div className="text-left">
                <p className="font-medium text-green-900 dark:text-green-100">
                  {uploadedFile.name}
                </p>
                <p className="text-xs text-green-700 dark:text-green-300">
                  Subido exitosamente
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRemove}
              className="hover:bg-green-100 dark:hover:bg-green-900"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}

      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}
    </div>
  );
};
