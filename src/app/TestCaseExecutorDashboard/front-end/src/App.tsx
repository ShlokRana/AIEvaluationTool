import { Routes, Route } from "react-router-dom";
import React, { useState, useEffect } from "react";

import "./App.css";
import LoginPage from "./components/Login/LoginPage";
import TestRunsPage from "./components/test-runs/TestRunsPage";
import TestRunDetails from "./components/test-run-details/TestRunDetailsPage";
import NewTestRunPage from "./components/new-test-run/NewTestRunPage";
import DevConfigPage from "./components/DevConfig/DevConfig";
import ContinueRunPage from "./components/continue-test-run/ContinueTestRunPage";
import Sidebar from "./components/common/sidebar/sidebar";
import Analysis from "./components/Analysis/Analysis";
import { redirectToLogin } from "./utils/auth";


function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const hash = window.location.hash.replace(/^#/, "");
    if (hash) {
      const values = Object.fromEntries(new URLSearchParams(hash));
      if (values.access_token && values.refresh_token) {
        localStorage.setItem("access_token", values.access_token);
        localStorage.setItem("refresh_token", values.refresh_token);
        if (values.user_name) localStorage.setItem("user_name", values.user_name);
        if (values.role) localStorage.setItem("role", values.role);
        window.history.replaceState({}, document.title, window.location.pathname + window.location.search);
        setIsAuthenticated(true);
        setLoading(false);
        return;
      }
    }

    const token = localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      return;
    }

    // Validate token with backend
    const tdmsBaseUrl =
      process.env.REACT_APP_TDMS_API_BASE_URL || "/tdms-api";
    const validateToken = async () => {
      try {
        const response = await fetch(`${tdmsBaseUrl}/api/users/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          credentials: "include",
        });

        if (!response.ok) {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          localStorage.removeItem("user_name");
          localStorage.removeItem("role");
          setIsAuthenticated(false);
          setLoading(false);
          return;
        }
        setIsAuthenticated(true);
      } catch (error) {
        setIsAuthenticated(false);
      } finally {
        setLoading(false);
      }
    };

    validateToken();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  const AuthenticatedApp = () => (
    <div className="app-container">
      <div className="sidebar">
        <Sidebar onLogout={() => setIsAuthenticated(false)} />
      </div>

      <main className="main-content">
        <Routes>
          <Route path="/" element={<TestRunsPage />} />
          <Route path="/test-runs/:runName" element={<TestRunDetails />} />
          <Route path="/create-test-run" element={<NewTestRunPage />} />
          <Route path="/continue-run/:runName" element={<ContinueRunPage />} />
          <Route path="/__dev/config" element={<DevConfigPage />} />
          <Route path="/analyse/:runName" element={<Analysis/>} />
        </Routes>
      </main>
    </div>
  );

  return (
    <Routes>
      <Route
        path="/login"
        element={<LoginPage />}
      />
      <Route
        path="/*"
        element={
          isAuthenticated ? <AuthenticatedApp /> : <LoginPage />
        }
      />
    </Routes>
  );
}

export default App;
