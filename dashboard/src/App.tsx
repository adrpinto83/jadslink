import React from "react";
import { useAuthStore } from "./stores/auth";
import { Navigate, Outlet } from "react-router-dom";

const App: React.FC = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // If authenticated, render the child routes (which will be the dashboard layout)
  return <Outlet />;
};

export default App;
