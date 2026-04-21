import { toast } from 'sonner';

type ToastType = 'success' | 'error' | 'info' | 'warning' | 'loading';

interface ToastOptions {
  description?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export const useToast = () => {
  return {
    success: (message: string, options?: ToastOptions) => {
      toast.success(message, {
        description: options?.description,
        duration: options?.duration || 3000,
        action: options?.action,
      });
    },
    error: (message: string, options?: ToastOptions) => {
      toast.error(message, {
        description: options?.description,
        duration: options?.duration || 5000,
        action: options?.action,
      });
    },
    info: (message: string, options?: ToastOptions) => {
      toast.info(message, {
        description: options?.description,
        duration: options?.duration || 3000,
        action: options?.action,
      });
    },
    warning: (message: string, options?: ToastOptions) => {
      toast.warning(message, {
        description: options?.description,
        duration: options?.duration || 4000,
        action: options?.action,
      });
    },
    loading: (message: string) => {
      return toast.loading(message);
    },
    dismiss: (id?: string | number) => {
      toast.dismiss(id);
    },
  };
};
