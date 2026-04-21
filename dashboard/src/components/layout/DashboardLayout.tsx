import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar'; // We will create this next

const DashboardLayout: React.FC = () => {
  return (
    <div className="flex min-h-screen bg-white">
      <Sidebar />
      <main className="flex-1 p-6 bg-gradient-to-br from-blue-50 to-indigo-50">
        <Outlet />
      </main>
    </div>
  );
};

export default DashboardLayout;
