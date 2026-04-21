import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './globals.css';;
import 'leaflet/dist/leaflet.css'; // Import Leaflet CSS
import App from './App.tsx'
import { createBrowserRouter, RouterProvider, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Login from './pages/Login.tsx';
import Register from './pages/Register.tsx';
import Root from './Root.tsx';
import DashboardLayout from './components/layout/DashboardLayout.tsx';
import Dashboard from './pages/Dashboard.tsx';
import Nodes from './pages/Nodes.tsx';
import NodeDetail from './pages/NodeDetail.tsx';
import Tickets from './pages/Tickets.tsx';
import Sessions from './pages/Sessions.tsx';
import Plans from './pages/Plans.tsx';
import Settings from './pages/Settings.tsx';
import Billing from './pages/Billing.tsx';
import Reports from './pages/Reports.tsx';
import DashboardAnalytics from './pages/DashboardAnalytics.tsx';
import Admin from './pages/Admin.tsx';
import { ThemeProvider } from "./components/theme-provider";
import { Toaster } from "sonner";

const queryClient = new QueryClient();

const router = createBrowserRouter([
  {
    path: "/login",
    element: <Login />,
  },
  {
    path: "/register",
    element: <Register />,
  },
  {
    path: "/",
    element: <Root />,
  },
  {
    path: "/dashboard",
    element: <App />,
    children: [
      {
        path: "",
        element: <DashboardLayout />,
        children: [
          {
            index: true,
            element: <Dashboard />
          },
          {
            path: "nodes",
            element: <Nodes />,
          },
          {
            path: "nodes/:nodeId",
            element: <NodeDetail />,
          },
          {
            path: "tickets",
            element: <Tickets />,
          },
          {
            path: "sessions",
            element: <Sessions />,
          },
          {
            path: "plans",
            element: <Plans />,
          },
          {
            path: "settings",
            element: <Settings />,
          },
          {
            path: "billing",
            element: <Billing />,
          },
          {
            path: "reports",
            element: <Reports />,
          },
          {
            path: "analytics",
            element: <DashboardAnalytics />,
          },
          {
            path: "admin",
            element: <Admin />,
          }
        ]
      }
    ]
  },
  {
    path: "*",
    element: <Navigate to="/" replace />
  } // Fallback route
]);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider defaultTheme="system" enableSystem>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
      <Toaster />
    </ThemeProvider>
  </StrictMode>,
)
