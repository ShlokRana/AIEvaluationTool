import { Routes, Route } from "react-router-dom";
import React from 'react';
import logo from './logo.svg';
import './App.css';
import TestRunsPage from './components/test-runs/TestRunsPage';
import TestRunDetails from './components/test-run-details/TestRunDetailsPage';

import Navbar from "./components/common/Navbar";
import NewTestRunPage from "./components/new-test-run/NewTestRunPage";
import DevConfigPage from "./components/DevConfig/DevConfig";
import ContinueRunPage from "./components/continue-test-run/ContinueTestRunPage";


function App() {
  return (
     <div className="app-container">
        <Navbar /> {/* Add the Navbar here */}
        <Routes>
          <Route path="/" element={<TestRunsPage />} />
          
          {/* 👇 THIS is the route you're navigating to */}
          <Route path="/test-runs/:runName" element={<TestRunDetails />} />
          <Route path="/create-test-run" element={<NewTestRunPage />} />
          <Route path="/continue-test-run" element={<ContinueRunPage />} />
          <Route path="/__dev/config" element={<DevConfigPage />} />
        </Routes>
     </div>
    
  );
}

export default App;
