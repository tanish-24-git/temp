import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import { Upload } from './pages/Upload';
import { Submissions } from './pages/Submissions';
import { Results } from './pages/Results';
import AdminDashboard from './pages/AdminDashboard';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="upload" element={<Upload />} />
          <Route path="submissions" element={<Submissions />} />
          <Route path="results/:id" element={<Results />} />
          <Route path="admin" element={<AdminDashboard />} /> {/* Phase 2: Admin Dashboard */}
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
