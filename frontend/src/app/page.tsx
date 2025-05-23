'use client';

import { useState, useEffect } from 'react';
import TaskForm from '@/components/TaskForm';
import TaskHistory from '@/components/TaskHistory';
import { checkApiHealth } from '@/services/api';
import { useTheme } from '@/context/ThemeContext';
import { FiMenu, FiX, FiSettings, FiSun, FiMoon, FiUser, FiLogOut, FiChevronLeft, FiPlus, FiFolder } from 'react-icons/fi';

export default function Home() {
  const [apiConnected, setApiConnected] = useState<boolean | null>(null);
  const [checking, setChecking] = useState<boolean>(true);
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [settingsOpen, setSettingsOpen] = useState<boolean>(false);
  const { darkMode, toggleDarkMode } = useTheme();

  useEffect(() => {
    const checkConnection = async () => {
      try {
        setChecking(true);
        const isHealthy = await checkApiHealth();
        setApiConnected(isHealthy);
      } catch (error) {
        console.error('Error checking API health:', error);
        setApiConnected(false);
      } finally {
        setChecking(false);
      }
    };

    checkConnection();
  }, []);

  const handleTaskSubmit = (taskId: string) => {
    console.log(`Task submitted with ID: ${taskId}`);
    setSelectedTaskId(taskId);
  };

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const toggleSettings = () => {
    setSettingsOpen(!settingsOpen);
  };

  // toggleDarkMode is now provided by the ThemeContext

  return (
    <div className={`flex h-screen ${darkMode ? 'bg-gray-900 text-gray-100' : 'bg-gray-100 text-gray-900'}`}>
      {/* Sidebar */}
      <div 
        className={`${sidebarOpen ? 'w-72' : 'w-0'} ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border-r transition-all duration-300 overflow-hidden flex flex-col z-10`}
      >
        <div className={`p-4 flex justify-between items-center ${darkMode ? 'border-gray-700' : 'border-gray-200'} border-b`}>
          <div className="flex items-center">
            <h2 className={`text-lg font-medium ${darkMode ? 'text-gray-200' : 'text-gray-800'}`}>Task History</h2>
          </div>
          <button 
            onClick={toggleSidebar}
            className={`p-2 rounded-full ${darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'} transition-colors`}
            aria-label="Close sidebar"
          >
            <FiChevronLeft className={`w-5 h-5 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`} />
          </button>
        </div>
        
        {/* New Task Button */}
        <div className="px-4 py-3">
          <button 
            className={`w-full flex items-center justify-center space-x-2 px-4 py-2 rounded-full ${darkMode ? 'bg-orange-500 hover:bg-orange-600' : 'bg-blue-500 hover:bg-blue-600'} text-white transition-colors`}
            onClick={() => {
              toggleSidebar();
              // Focus on the task input after a short delay to allow animation
              setTimeout(() => {
                const taskInput = document.getElementById('taskDescription');
                if (taskInput) {
                  taskInput.focus();
                }
              }, 300);
            }}
          >
            <FiPlus className="w-4 h-4" />
            <span>New Task</span>
          </button>
        </div>
        
        <div className="flex-grow overflow-auto">
          <TaskHistory onTaskSelect={setSelectedTaskId} />
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden relative">
        {/* Settings Popup */}
        {settingsOpen && (
          <div className="absolute right-4 top-14 z-20">
            <div className={`${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border rounded-lg shadow-lg w-64 py-2 overflow-hidden`}>
              <div className="px-4 py-2 border-b border-gray-700">
                <h3 className={`font-medium ${darkMode ? 'text-gray-200' : 'text-gray-800'}`}>Settings</h3>
              </div>
              <div className="p-2">
                <button 
                  className={`w-full text-left px-4 py-2 rounded-md flex items-center ${darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}
                  onClick={toggleDarkMode}
                >
                  {darkMode ? 
                    <FiSun className="mr-2 w-5 h-5 text-yellow-400" /> : 
                    <FiMoon className="mr-2 w-5 h-5 text-blue-400" />
                  }
                  <span>{darkMode ? 'Light Mode' : 'Dark Mode'}</span>
                </button>
                <button 
                  className={`w-full text-left px-4 py-2 rounded-md flex items-center ${darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}
                >
                  <FiUser className="mr-2 w-5 h-5" />
                  <span>Profile</span>
                </button>
                <button 
                  className={`w-full text-left px-4 py-2 rounded-md flex items-center ${darkMode ? 'hover:bg-gray-700 text-red-400' : 'hover:bg-gray-100 text-red-500'}`}
                >
                  <FiLogOut className="mr-2 w-5 h-5" />
                  <span>Logout</span>
                </button>
              </div>
            </div>
          </div>
        )}
        
        {/* Header with connection status and settings */}
        <div className="flex justify-between items-center p-4">
          <div className="flex items-center">
            {!sidebarOpen && (
              <button 
                onClick={toggleSidebar}
                className={`p-2 mr-2 rounded-full ${darkMode ? 'hover:bg-gray-800' : 'hover:bg-gray-100'} transition-colors`}
                aria-label="Open sidebar"
              >
                <FiChevronLeft className={`w-5 h-5 transform rotate-180 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`} />
              </button>
            )}
            {!sidebarOpen && <h1 className={`text-lg font-medium ${darkMode ? 'text-gray-200' : 'text-gray-800'}`}>Autonomous AI Agent</h1>}
          </div>
          <div className="flex items-center space-x-2">
            {checking ? (
              <div className={`px-3 py-1 ${darkMode ? 'bg-blue-900 text-blue-300' : 'bg-blue-50 text-blue-600'} rounded-full text-sm flex items-center`}>
                <div className={`animate-spin rounded-full h-3 w-3 border-t-2 border-b-2 ${darkMode ? 'border-blue-300' : 'border-blue-500'} mr-2`}></div>
                Connecting...
              </div>
            ) : apiConnected === false ? (
              <div className={`px-3 py-1 ${darkMode ? 'bg-red-900 text-red-300' : 'bg-red-50 text-red-600'} rounded-full text-sm`}>
                Backend disconnected
              </div>
            ) : apiConnected === true ? (
              <div className={`px-3 py-1 ${darkMode ? 'bg-green-900 text-green-300' : 'bg-green-50 text-green-600'} rounded-full text-sm`}>
                Connected
              </div>
            ) : null}
            <button 
              onClick={toggleSettings}
              className={`p-2 rounded-full ${darkMode ? 'hover:bg-gray-800' : 'hover:bg-gray-100'} transition-colors`}
              aria-label="Settings"
            >
              <FiSettings className={`w-5 h-5 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`} />
            </button>
          </div>
        </div>

        {/* Main Content Area */}
        <main className="flex-1 flex flex-col items-center justify-center overflow-auto px-4 py-12">
          <div className="w-full max-w-2xl">
            {/* Claude-style welcome message */}
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center">
                <div className={`w-6 h-6 rounded-full ${darkMode ? 'bg-orange-500' : 'bg-orange-400'} flex items-center justify-center mr-3`}>
                  <svg className="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 16L7 11L8.4 9.55L12 13.15L15.6 9.55L17 11L12 16Z" fill="currentColor" />
                  </svg>
                </div>
                <h1 className={`text-2xl font-light ${darkMode ? 'text-gray-200' : 'text-gray-800'}`}>Welcome, User</h1>
              </div>
            </div>
            
            {/* Task submission form */}
            <div className={`${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border rounded-xl overflow-hidden`}>
              <TaskForm onTaskSubmit={handleTaskSubmit} />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
