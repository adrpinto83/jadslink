import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, Wifi, Ticket, BookUser, BarChart, Settings, CreditCard, Shield, LogOut, Package, Users } from 'lucide-react';
import { useAuthStore } from '@/stores/auth';
import { ModeToggle } from '@/components/theme-toggle';
import AppLogo from '@/components/AppLogo';

const Sidebar: React.FC = () => {
  const logout = useAuthStore((state) => state.logout);
  const user = useAuthStore((state) => state.user);

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center px-4 py-2 text-gray-700 rounded-lg transition-all duration-200 hover:bg-blue-100 hover:text-blue-700 ${
      isActive ? 'bg-blue-100 text-blue-700 font-semibold' : ''
    }`;

  return (
    <aside className="w-64 flex-shrink-0 p-4 bg-white border-r border-gray-200 shadow-sm">
      <div className="flex items-center mb-8">
        <AppLogo size="sm" className="mr-2" />
        <h1 className="text-xl font-bold text-gray-900">JADSlink</h1>
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
        <NavLink to="/dashboard/plans" className={navLinkClass}>
          <Package className="w-5 h-5 mr-3" />
          Planes
        </NavLink>
        <NavLink to="/dashboard/reports" className={navLinkClass}>
          <BarChart className="w-5 h-5 mr-3" />
          Reportes
        </NavLink>
        <NavLink to="/dashboard/analytics" className={navLinkClass}>
          <BarChart className="w-5 h-5 mr-3" />
          Analytics
        </NavLink>
        <NavLink to="/dashboard/settings" className={navLinkClass}>
          <Settings className="w-5 h-5 mr-3" />
          Ajustes
        </NavLink>
        <NavLink to="/dashboard/billing" className={navLinkClass}>
          <CreditCard className="w-5 h-5 mr-3" />
          Facturación
        </NavLink>
        {/* Equipo: Solo visible para operadores (no superadmin) */}
        {user?.role !== 'superadmin' && (
          <NavLink to="/dashboard/team" className={navLinkClass}>
            <Users className="w-5 h-5 mr-3" />
            Equipo
          </NavLink>
        )}
        <NavLink to="/dashboard/admin" className={navLinkClass}>
          <Shield className="w-5 h-5 mr-3" />
          Admin
        </NavLink>
      </nav>
      <div className="mt-auto absolute bottom-4 w-56 space-y-2">
        <button
          onClick={logout}
          className="flex items-center px-4 py-2 text-gray-700 rounded-lg transition-all duration-200 hover:bg-red-100 hover:text-red-700 w-full font-medium"
        >
          <LogOut className="w-5 h-5 mr-3" />
          Cerrar Sesión
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
