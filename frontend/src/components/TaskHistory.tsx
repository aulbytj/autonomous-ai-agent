'use client';

import { useTheme } from '@/context/ThemeContext';

interface TaskHistoryProps {
  onTaskSelect?: (taskId: string) => void;
}

/**
 * Simplified TaskHistory component to eliminate client-side errors
 */
export default function TaskHistory({ onTaskSelect }: TaskHistoryProps) {
  const { darkMode } = useTheme();

  // Return a simple static message instead of fetching tasks
  return (
    <div className="h-full flex flex-col">
      <div className={`flex flex-col items-center justify-center h-40 ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
        <svg className="w-12 h-12 mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
        </svg>
        <p>No tasks found</p>
      </div>
    </div>
  );
}
