import React, { useState, useEffect } from 'react';
import { Link, Outlet } from 'react-router-dom';
import { FileText, Upload, BarChart3, List, Settings } from 'lucide-react';
import { Onboarding } from '../onboarding/Onboarding';

export const Layout: React.FC = () => {
  const [showOnboarding, setShowOnboarding] = useState(false);

  useEffect(() => {
    // Check if user has seen onboarding
    const hasSeenOnboarding = localStorage.getItem('compliance-agent-onboarding-seen');
    if (hasSeenOnboarding !== 'true') {
      setShowOnboarding(true);
    }
  }, []);

  return (
    <div className="min-h-screen bg-gradient-subtle">
      {/* Onboarding Modal */}
      {showOnboarding && (
        <Onboarding onComplete={() => setShowOnboarding(false)} />
      )}

      <header className="border-b bg-white/90 backdrop-blur-sm sticky top-0 z-40 shadow-sm">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg">
              <FileText className="h-5 w-5 text-white" />
            </div>
            <h1 className="text-xl font-bold text-gray-900">Compliance Agent</h1>
          </div>
          <nav className="flex gap-6">
            <Link to="/" className="flex items-center gap-2 text-gray-700 hover:text-blue-600 transition-colors font-medium">
              <BarChart3 className="h-4 w-4" />
              Dashboard
            </Link>
            <Link to="/upload" className="flex items-center gap-2 text-gray-700 hover:text-blue-600 transition-colors font-medium">
              <Upload className="h-4 w-4" />
              Upload
            </Link>
            <Link to="/submissions" className="flex items-center gap-2 text-gray-700 hover:text-blue-600 transition-colors font-medium">
              <List className="h-4 w-4" />
              Submissions
            </Link>
            <span className="border-l border-gray-300"></span>
            <Link to="/admin" className="flex items-center gap-2 text-purple-700 hover:text-purple-500 transition-colors font-semibold">
              <Settings className="h-4 w-4" />
              Admin
            </Link>
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
};
