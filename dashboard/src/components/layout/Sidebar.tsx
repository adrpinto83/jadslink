import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, Wifi, Ticket, BookUser, BarChart, Settings, CreditCard, Shield, LogOut } from 'lucide-react';
import { useAuthStore } from '@/stores/auth';

const Sidebar: React.FC = () => {
  const logout = useAuthStore((state) => state.logout);

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center px-4 py-2 text-gray-700 rounded-lg hover:bg-gray-200 dark:text-gray-200 dark:hover:bg-gray-700 ${
      isActive ? 'bg-gray-300 dark:bg-gray-600' : ''
    }`;

  return (
    <aside className="w-64 flex-shrink-0 p-4 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700">
      <div className="flex items-center mb-8">
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">JADSlink</h1>
      </div>
      <nav className="space-y-2">
        <NavLink to="/dashboard" end className={navLinkClass}>
          <Home className="w-5 h-5 mr-3" />
          Inicio
        </NavLink>
        <NavLink to="/dashboard/nodes" className={navLinkClass}>
          <Wifi className="w-5 h-5 mr-3" />
          Nodos
        </NavLink>
        <NavLink to="/dashboard/tickets" className={navLinkClass}>
          <Ticket className="w-5 h-5 mr-3" />
          Tickets
        </NavLink>
        <NavLink to="/dashboard/sessions" className={navLinkClass}>
          <BookUser className="w-5 h-5 mr-3" />
          Sesiones
        </NavLink>
        {/* Add other links here based on GEMINI.md */}
        <NavLink to="/dashboard/reports" className={navLinkClass}>
          <BarChart className="w-5 h-5 mr-3" />
          Reportes
        </NavLink>
        <NavLink to="/dashboard/settings" className={navLinkClass}>
          <Settings className="w-5 h-5 mr-3" />
          Ajustes
        </NavLink>
        <NavLink to="/dashboard/billing" className={navLinkClass}>
          <CreditCard className="w-5 h-5 mr-3" />
          Facturación
        </NavLink>
        <NavLink to="/dashboard/admin" className={navLinkClass}>
          <Shield className="w-5 h-5 mr-3" />
          Admin
        </NavLink>
      </nav>
      <div className="mt-auto absolute bottom-4 w-56">
        <button onClick={logout} className="flex items-center px-4 py-2 text-gray-700 rounded-lg hover:bg-gray-200 dark:text-gray-200 dark:hover:bg-gray-700 w-full">
          <LogOut className="w-5 h-5 mr-3" />
          Cerrar Sesión
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
