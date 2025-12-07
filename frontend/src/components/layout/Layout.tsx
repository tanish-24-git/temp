import React from 'react';
import { Link, Outlet } from 'react-router-dom';
import { FileText, Upload, BarChart3, List, Settings } from 'lucide-react';

export const Layout: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b bg-white">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="h-6 w-6 text-blue-600" />
            <h1 className="text-xl font-bold text-gray-900">Compliance Agent</h1>
          </div>
          <nav className="flex gap-6">
            <Link to="/" className="flex items-center gap-2 text-gray-700 hover:text-blue-600 transition-colors">
              <BarChart3 className="h-4 w-4" />
              Dashboard
            </Link>
            <Link to="/upload" className="flex items-center gap-2 text-gray-700 hover:text-blue-600 transition-colors">
              <Upload className="h-4 w-4" />
              Upload
            </Link>
            <Link to="/submissions" className="flex items-center gap-2 text-gray-700 hover:text-blue-600 transition-colors">
              <List className="h-4 w-4" />
              Submissions
            </Link>
            <span className="border-l border-gray-300"></span>
            <Link to="/admin" className="flex items-center gap-2 text-purple-700 hover:text-purple-500 transition-colors font-medium">
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
