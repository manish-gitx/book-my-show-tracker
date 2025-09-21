import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Film, Bell, TestTube } from 'lucide-react';

const Header = () => {
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center space-x-2">
            <Film className="h-8 w-8 text-primary-600" />
            <span className="text-xl font-bold text-gray-900">
              BookMyShow Tracker
            </span>
          </Link>

          <nav className="flex items-center space-x-6">
            <Link
              to="/"
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive('/')
                  ? 'bg-primary-100 text-primary-700'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              <Film className="h-4 w-4" />
              <span>Home</span>
            </Link>

            <Link
              to="/subscriptions"
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive('/subscriptions')
                  ? 'bg-primary-100 text-primary-700'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              <Bell className="h-4 w-4" />
              <span>Subscriptions</span>
            </Link>

            <Link
              to="/test"
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive('/test')
                  ? 'bg-primary-100 text-primary-700'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              <TestTube className="h-4 w-4" />
              <span>Test</span>
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;
