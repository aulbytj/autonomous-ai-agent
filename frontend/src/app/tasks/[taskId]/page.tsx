'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import TaskStatus from '@/components/TaskStatus';
import TaskReplay from '@/components/TaskReplay';
import { useTheme } from '@/context/ThemeContext';
import { FiPlay, FiSun, FiMoon } from 'react-icons/fi';

export default function TaskDetailPage() {
  const params = useParams();
  const taskId = params.taskId as string;
  const [showReplay, setShowReplay] = useState(false);
  const { darkMode, toggleDarkMode } = useTheme();

  return (
    <main className={`container mx-auto px-4 py-8 max-w-5xl ${darkMode ? 'bg-gray-900 text-gray-100' : 'bg-gray-100 text-gray-900'}`}>
      <div className="text-center mb-10">
        <h1 className={`text-4xl font-bold ${darkMode ? 'text-gray-100' : 'text-gray-900'} mb-2`}>Task Details</h1>
        <p className={`text-xl ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>View task progress and results</p>
      </div>

      <div className="flex justify-end mb-4">
        <button
          onClick={toggleDarkMode}
          className={`px-4 py-2 rounded-md mr-2 ${darkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-200 hover:bg-gray-300'} flex items-center`}
        >
          {darkMode ? <FiSun className="mr-2" /> : <FiMoon className="mr-2" />}
          {darkMode ? 'Light Mode' : 'Dark Mode'}
        </button>
        <button
          onClick={() => setShowReplay(!showReplay)}
          className={`px-4 py-2 rounded-md flex items-center ${darkMode ? 'bg-orange-600 hover:bg-orange-700' : 'bg-blue-600 hover:bg-blue-700'} text-white`}
        >
          <FiPlay className="mr-2" />
          {showReplay ? 'Hide Replay' : 'Show Replay'}
        </button>
      </div>

      {showReplay ? (
        <div className="mb-8">
          <TaskReplay taskId={taskId} onClose={() => setShowReplay(false)} />
        </div>
      ) : null}

      <TaskStatus taskId={taskId} />
    </main>
  );
}
