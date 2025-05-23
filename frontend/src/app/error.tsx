'use client';

import { useEffect } from 'react';
import { useTheme } from '@/context/ThemeContext';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const { darkMode } = useTheme();

  useEffect(() => {
    // Log the error to an error reporting service
    console.error('Next.js Error Boundary caught error:', error);
  }, [error]);

  return (
    <div className={`${darkMode ? 'bg-gray-900 text-gray-100' : 'bg-gray-100 text-gray-900'} flex min-h-screen flex-col items-center justify-center p-4`}>
      <div className={`${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border rounded-xl p-6 w-full max-w-md shadow-lg`}>
        <h2 className={`text-xl font-semibold mb-4 ${darkMode ? 'text-red-400' : 'text-red-600'}`}>
          Something went wrong
        </h2>
        <p className={`mb-6 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
          An unexpected error occurred. Please try again or refresh the page.
        </p>
        <div className="flex space-x-4">
          <button
            onClick={() => reset()}
            className={`px-4 py-2 rounded-md ${
              darkMode 
                ? 'bg-orange-500 hover:bg-orange-600 text-white' 
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            } transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
              darkMode ? 'focus:ring-orange-500' : 'focus:ring-blue-500'
            }`}
          >
            Try again
          </button>
          <button
            onClick={() => window.location.reload()}
            className={`px-4 py-2 rounded-md ${
              darkMode 
                ? 'bg-gray-700 hover:bg-gray-600 text-gray-300' 
                : 'bg-gray-100 hover:bg-gray-200 text-gray-800'
            } transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
              darkMode ? 'focus:ring-gray-600' : 'focus:ring-gray-300'
            }`}
          >
            Refresh
          </button>
        </div>
      </div>
    </div>
  );
}
