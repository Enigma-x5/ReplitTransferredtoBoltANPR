import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "@/auth/AuthContext";
import { ProtectedRoute } from "@/auth/ProtectedRoute";
import { AppLayout } from "@/components/AppLayout";

import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import CamerasPage from "./pages/CamerasPage";
import UploadsPage from "./pages/UploadsPage";
import EventsPage from "./pages/EventsPage";
import ReviewPage from "./pages/ReviewPage";
import BOLOsPage from "./pages/BOLOsPage";
import SystemStatusPage from "./pages/SystemStatusPage";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Navigate to="/dashboard" replace />
                </ProtectedRoute>
              }
            />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <DashboardPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/cameras"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <CamerasPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/uploads"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <UploadsPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/events"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <EventsPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/review"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <ReviewPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/bolos"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <BOLOsPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/system"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <SystemStatusPage />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
