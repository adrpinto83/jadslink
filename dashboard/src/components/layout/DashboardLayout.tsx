import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar'; // We will create this next

const DashboardLayout: React.FC = () => {
  return (
    <div className="flex min-h-screen bg-gray-100 dark:bg-gray-900">
      <Sidebar />
      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  );
};

export default DashboardLayout;
