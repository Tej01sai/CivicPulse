import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import IntakePage from './pages/IntakePage';
import VolunteersPage from './pages/VolunteersPage';
import AssignmentsPage from './pages/AssignmentsPage';
import { api } from './lib/api';

export default function App() {
  const [criticalCount, setCriticalCount] = useState(0);

  useEffect(() => {
    api.getStats()
      .then(s => setCriticalCount(s.critical_needs))
      .catch(() => {});
  }, []);

  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar criticalCount={criticalCount} />
        <main className="main-content">
          <Routes>
            <Route path="/"            element={<Dashboard />} />
            <Route path="/intake"      element={<IntakePage />} />
            <Route path="/volunteers"  element={<VolunteersPage />} />
            <Route path="/assignments" element={<AssignmentsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
