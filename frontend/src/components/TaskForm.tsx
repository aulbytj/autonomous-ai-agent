'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { submitTask, testTaskSubmission, TaskSubmitRequest } from '@/services/api';
import { useTheme } from '@/context/ThemeContext';

interface TaskFormProps {
  onTaskSubmit: (taskId: string) => void;
}

export default function TaskForm({ onTaskSubmit }: TaskFormProps) {
  const { darkMode } = useTheme();
  const [taskDescription, setTaskDescription] = useState('');
  const [priority, setPriority] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!taskDescription.trim()) {
      setError('Please enter a task description');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      console.log('Submitting task with description:', taskDescription);
      const taskRequest: TaskSubmitRequest = {
        task: taskDescription,
        context: {
          priority: priority,
        },
      };
      
      // First check if the API is available
      try {
        const response = await fetch('http://localhost:8098/api/health');
        if (!response.ok) {
          throw new Error(`API health check failed: ${response.status}`);
        }
      } catch (healthErr) {
        console.error('API health check error:', healthErr);
        setError('Cannot connect to the backend API. Please make sure the backend server is running.');
        setIsSubmitting(false);
        return;
      }
      
      // If we get here, the API is available
      try {
        // First try the regular task submission
        const data = await submitTask(taskRequest);
        console.log('Task submitted successfully:', data);
        onTaskSubmit(data.task_id);
        setTaskDescription('');
        router.push(`/tasks/${data.task_id}`);
      } catch (submitError) {
        console.error('Regular task submission failed, trying test endpoint:', submitError);
        // If the regular submission fails, try the test endpoint
        try {
          const testData = await testTaskSubmission(taskRequest);
          console.log('Test task submission successful:', testData);
          onTaskSubmit(testData.task_id);
          setTaskDescription('');
          router.push(`/tasks/${testData.task_id}`);
        } catch (testError) {
          console.error('Test task submission also failed:', testError);
          throw testError; // Re-throw to be caught by the outer catch block
        }
      }
    } catch (err) {
      console.error('Error submitting task:', err);
      setError(`Failed to submit task: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="p-4">
      {error && (
        <div className={`${darkMode ? 'bg-red-900 text-red-300' : 'bg-red-50 text-red-600'} p-3 rounded-md mb-4`}>
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <textarea
            id="taskDescription"
            className={`w-full px-4 py-3 border-0 ${darkMode ? 'bg-gray-700 text-gray-100 placeholder-gray-400' : 'bg-gray-50 text-gray-800 placeholder-gray-400'} rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none transition-all`}
            rows={4}
            placeholder="How can I help you today? Describe your task in natural language..."
            value={taskDescription}
            onChange={(e) => setTaskDescription(e.target.value)}
            disabled={isSubmitting}
            required
          />
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex space-x-2">
            <div className={`flex items-center space-x-1 text-sm ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>
              <span>Priority:</span>
              <div className={`flex ${darkMode ? 'bg-gray-700' : 'bg-gray-100'} rounded-lg p-1`}>
                <button 
                  type="button"
                  className={`px-2 py-1 rounded-md text-xs font-medium transition-colors ${priority === 1 ? 
                    (darkMode ? 'bg-gray-600 text-gray-200' : 'bg-white shadow-sm text-gray-800') : 
                    (darkMode ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-700')}`}
                  onClick={() => setPriority(1)}
                  disabled={isSubmitting}
                >
                  Low
                </button>
                <button 
                  type="button"
                  className={`px-2 py-1 rounded-md text-xs font-medium transition-colors ${priority === 2 ? 
                    (darkMode ? 'bg-gray-600 text-gray-200' : 'bg-white shadow-sm text-gray-800') : 
                    (darkMode ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-700')}`}
                  onClick={() => setPriority(2)}
                  disabled={isSubmitting}
                >
                  Medium
                </button>
                <button 
                  type="button"
                  className={`px-2 py-1 rounded-md text-xs font-medium transition-colors ${priority === 3 ? 
                    (darkMode ? 'bg-gray-600 text-gray-200' : 'bg-white shadow-sm text-gray-800') : 
                    (darkMode ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-700')}`}
                  onClick={() => setPriority(3)}
                  disabled={isSubmitting}
                >
                  High
                </button>
              </div>
            </div>
          </div>
          
          <button
            type="submit"
            className={`py-2 px-6 ${darkMode ? 'bg-orange-500 hover:bg-orange-600' : 'bg-blue-600 hover:bg-blue-700'} text-white font-medium rounded-full focus:outline-none focus:ring-2 focus:ring-opacity-50 transition-colors flex items-center ${
              isSubmitting ? 'opacity-70 cursor-not-allowed' : ''
            } ${darkMode ? 'focus:ring-orange-500' : 'focus:ring-blue-500'}`}
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing...
              </>
            ) : (
              'Submit'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
