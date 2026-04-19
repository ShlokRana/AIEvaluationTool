import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import { isAuthenticated, parseUrlTokens } from "./utils/auth";
import TestCases from "./pages/TestCases";
import Responses from "./pages/Responses";
import Users from "./pages/Users";
import UserHistory from "./pages/UserHistory";
import NotFound from "./pages/NotFound";
import Targets from "./pages/Targets";
import Prompts from "./pages/Prompts";
import DomainList from "./pages/Domains";
import StrategyList from "./pages/Strategies";
import LlmPrompts from "./pages/LlmPrompts";
import LanguageList from "./pages/Language";
import TestPlans from "./pages/TestPlans";
import Metrics from "./pages/Metrics";


const queryClient = new QueryClient();
const routerBasename = import.meta.env.BASE_URL;

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter basename={routerBasename}>
        {parseUrlTokens()}
        <Routes>
          <Route path="/" element={isAuthenticated() ? <Navigate to="/dashboard" replace /> : <Login />} />
          <Route path="/dashboard" element={isAuthenticated() ? <Dashboard /> : <Navigate to="/" replace />} />
          <Route path="/test-cases" element={isAuthenticated() ? <TestCases /> : <Navigate to="/" replace />} />
          <Route path="/targets" element={isAuthenticated() ? <Targets /> : <Navigate to="/" replace />} />
          <Route path="/responses" element={isAuthenticated() ? <Responses /> : <Navigate to="/" replace />} />
          <Route path="/prompts" element={isAuthenticated() ? <Prompts/> : <Navigate to="/" replace />} />
          <Route path="/domains" element={isAuthenticated() ? <DomainList/> : <Navigate to="/" replace />} />
          <Route path="/strategies" element={isAuthenticated() ? <StrategyList/> : <Navigate to="/" replace />} />
          <Route path="/llm-prompts" element={isAuthenticated() ? <LlmPrompts/> : <Navigate to="/" replace />} />
          <Route path="/languages" element={isAuthenticated() ? <LanguageList /> : <Navigate to="/" replace />} />
          <Route path="/users" element={isAuthenticated() ? <Users /> : <Navigate to="/" replace />} />
          <Route path="/test-plans" element={isAuthenticated() ? <TestPlans /> : <Navigate to="/" replace />} />
          <Route path="/metrics" element={isAuthenticated() ? <Metrics /> : <Navigate to="/" replace />} />
          <Route path="/user-history/:username" element={isAuthenticated() ? <UserHistory /> : <Navigate to="/" replace />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
