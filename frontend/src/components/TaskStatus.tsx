'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { getTaskStatus, TaskResponse, SubtaskResponse } from '../services/api';

const INITIAL_RECONNECT_DELAY = 1000; // 1 second
const MAX_RECONNECT_ATTEMPTS = 5;
const MAX_RECONNECT_DELAY = 30000; // 30 seconds

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected';

interface TaskStatusProps {
  taskId: string;
  darkMode?: boolean;
}

const TaskStatus: React.FC<TaskStatusProps> = ({ taskId, darkMode = false }) => {
  // State management
  const [task, setTask] = useState<TaskResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [isReconnecting, setIsReconnecting] = useState(false);

  // Refs for WebSocket and reconnection
  const ws = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const router = useRouter();

  // Refs for callbacks to avoid dependency issues
  const handleWebSocketMessageRef = useRef<(event: MessageEvent) => void>(() => {});
  const handleWebSocketErrorRef = useRef<(event: Event) => void>(() => {});
  const attemptReconnectRef = useRef<() => Promise<void>>(async () => {});

  // Function to calculate reconnect delay with exponential backoff
  const getReconnectDelay = useCallback((attempt: number): number => {
    return Math.min(INITIAL_RECONNECT_DELAY * Math.pow(2, attempt), MAX_RECONNECT_DELAY);
  }, []);

  // Function to safely close WebSocket
  const closeWebSocket = useCallback((code = 1000, reason = 'Normal closure') => {
    if (ws.current) {
      try {
        if (ws.current.readyState === WebSocket.OPEN) {
          ws.current.close(code, reason);
        }
      } catch (e) {
        console.warn('Error closing WebSocket:', e);
      } finally {
        ws.current = null;
      }
    }
  }, []);

  // Define the WebSocket message handler
  const handleWebSocketMessage = useCallback((event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data);
      if (data.task) {
        // Map the task data to match the TaskResponse interface
        const taskResponse: TaskResponse = {
          task_id: data.task.task_id || '',
          status: data.task.status || 'PENDING',
          result: data.task.result || null,
          error: data.task.error || null,
          progress: data.task.progress || 0,
          subtasks: (data.task.subtasks || []).map((st: any) => ({
            id: st.id || '',
            type: st.type || '',
            status: st.status || 'PENDING',
            result: st.result || null,
            error: st.error || null,
            progress: st.progress || 0,
            created_at: st.created_at || new Date().toISOString(),
            updated_at: st.updated_at || new Date().toISOString()
          })) as SubtaskResponse[],
          created_at: data.task.created_at || new Date().toISOString(),
          updated_at: data.task.updated_at || new Date().toISOString()
        };
        setTask(taskResponse);
        setError('');
        setConnectionStatus('connected');
      } else if (data.error) {
        setError(data.error);
      }
    } catch (e) {
      console.error('Error parsing WebSocket message:', e);
    }
  }, []);

  // WebSocket error handler
  const handleWebSocketError = useCallback((error: Event) => {
    console.error('WebSocket error:', error);
    setConnectionStatus('disconnected');
  }, []);

  // Forward declaration of initWebSocket to avoid TypeScript errors
  let initWebSocket: () => Promise<void>;

  // Reconnection logic
  const attemptReconnect = useCallback(async (): Promise<void> => {
    if (reconnectAttempts.current >= MAX_RECONNECT_ATTEMPTS) {
      setError('Connection lost. Please refresh the page to reconnect.');
      setConnectionStatus('disconnected');
      setIsReconnecting(false);
      return;
    }

    // Clear any existing timeout to prevent multiple reconnection attempts
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }

    const delay = getReconnectDelay(reconnectAttempts.current);
    const attemptNumber = reconnectAttempts.current + 1;
    reconnectAttempts.current = attemptNumber;

    // Show reconnection status to the user
    setConnectionStatus('connecting');
    setIsReconnecting(true);
    console.log(`Attempting to reconnect (${attemptNumber}/${MAX_RECONNECT_ATTEMPTS}) in ${delay}ms`);

    try {
      await new Promise<void>((resolve) => {
        reconnectTimeout.current = setTimeout(async () => {
          console.log(`Reconnection attempt ${attemptNumber} in progress...`);

          try {
            // Only attempt to reconnect if we don't have a valid connection
            if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
              try {
                await initWebSocket();
              } catch (initError) {
                console.error('Error during WebSocket initialization:', initError);
                // Don't rethrow, just log the error
              }
            } else {
              console.log('WebSocket already connected, skipping reconnection');
              setConnectionStatus('connected');
            }
            resolve();
          } catch (error) {
            console.error('Reconnection attempt failed:', error);
            // Schedule next attempt if we haven't exceeded max attempts
            if (reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS && attemptReconnectRef.current) {
              // Use the ref to call itself to avoid stale closure issues
              setTimeout(() => {
                if (attemptReconnectRef.current) {
                  attemptReconnectRef.current();
                }
              }, 1000); // Add a small delay before retrying
            } else {
              setError('Failed to reconnect. Please refresh the page to try again.');
              setConnectionStatus('disconnected');
            }
          } finally {
            setIsReconnecting(false);
          }
        }, delay);
      });
    } catch (error) {
      console.error('Error in reconnection logic:', error);
      setIsReconnecting(false);
    }
  }, [getReconnectDelay]);

  // Update refs when callbacks change
  useEffect(() => {
    handleWebSocketMessageRef.current = handleWebSocketMessage;
    handleWebSocketErrorRef.current = handleWebSocketError;
    attemptReconnectRef.current = attemptReconnect;
  }, [handleWebSocketMessage, handleWebSocketError, attemptReconnect]);

  // Initialize WebSocket connection
  initWebSocket = useCallback(async (): Promise<void> => {
    if (!taskId) {
      console.error('No taskId provided for WebSocket connection');
      return;
    }

    // Close existing connection if any
    closeWebSocket(1000, 'Reinitializing connection');

    try {
      // Use the WebSocket URL from config if available, otherwise construct it
      // Check if window is defined (client-side only)
      if (typeof window === 'undefined') {
        console.log('WebSocket cannot be initialized on server side');
        return;
      }
      
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/ws/${taskId}`;

      console.log('Connecting to WebSocket:', wsUrl);

      // Create a promise that resolves when the connection is established
      const socket = await new Promise<WebSocket>((resolve, reject) => {
        try {
          const socket = new WebSocket(wsUrl);

          const cleanup = () => {
            socket.onopen = null;
            socket.onerror = null;
          };

          const onOpen = () => {
            cleanup();
            console.log('WebSocket connection established');
            resolve(socket);
          };

          const onError = (error: Event) => {
            cleanup();
            console.error('WebSocket connection error:', error);
            reject(new Error('Failed to connect to WebSocket'));
          };

          // Set initial handlers
          socket.onopen = onOpen;
          socket.onerror = onError;

          // Set a timeout for the connection attempt
          const timeout = setTimeout(() => {
            cleanup();
            reject(new Error('WebSocket connection timeout'));
            try {
              socket.close(1000, 'Connection timeout');
            } catch (e) {
              console.warn('Error closing socket after timeout:', e);
            }
          }, 10000); // 10 second timeout

          // Update handlers to clean up timeout
          socket.onopen = () => {
            clearTimeout(timeout);
            onOpen();
          };

          socket.onerror = (error) => {
            clearTimeout(timeout);
            onError(error);
          };
        } catch (error) {
          console.error('Error creating WebSocket:', error);
          reject(error);
        }
      });

      // Store the WebSocket instance
      ws.current = socket;

      // Set up close handler
      const handleClose = (event: CloseEvent) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setConnectionStatus('disconnected');

        // Only attempt to reconnect if the close was not normal (1000)
        if (event.code !== 1000) {
          console.log('Attempting to reconnect...');
          attemptReconnectRef.current?.();
        }
      };

      // Set up handlers using refs
      socket.onmessage = (event) => {
        if (handleWebSocketMessageRef.current) {
          handleWebSocketMessageRef.current(event);
        }
      };
      socket.onerror = (event) => {
        if (handleWebSocketErrorRef.current) {
          handleWebSocketErrorRef.current(event);
        }
      };
      socket.onclose = handleClose;

      // Update connection status
      setConnectionStatus('connected');
      reconnectAttempts.current = 0; // Reset reconnection attempts
    } catch (error) {
      console.error('Error initializing WebSocket:', error);
      setConnectionStatus('disconnected');
      setError(`Failed to connect: ${error instanceof Error ? error.message : 'Unknown error'}`);

      // Only attempt to reconnect if we haven't exceeded max attempts
      if (reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
        console.log('Scheduling reconnection attempt...');
        if (attemptReconnectRef.current) {
          attemptReconnectRef.current();
        }
      } else {
        setError('Failed to connect after multiple attempts. Please refresh the page to try again.');
      }
      
      // Don't re-throw the error to prevent unhandled promise rejections
      // This is a common source of the createUnhandledError in Next.js
    }
  }, [taskId, closeWebSocket]);

  // Initialize WebSocket and fetch initial task data
  useEffect(() => {
    // Skip execution during server-side rendering
    if (typeof window === 'undefined') {
      return;
    }
    
    if (!taskId) {
      setError('No task ID provided');
      setLoading(false);
      return;
    }

    // Initial task fetch
    const fetchInitialTask = async () => {
      try {
        const data = await getTaskStatus(taskId);
        if (!data) {
          setError('Task not found');
          return;
        }
        // Ensure the task data matches the TaskResponse interface
        const taskResponse: TaskResponse = {
          task_id: data.task_id || '',
          status: data.status || 'PENDING',
          result: data.result ?? null,
          error: data.error ?? null,
          progress: data.progress || 0,
          subtasks: (data.subtasks || []).map((st: any) => ({
            id: st.id || '',
            type: st.type || '',
            status: st.status || 'PENDING',
            result: st.result ?? null,
            error: st.error ?? null,
            progress: st.progress || 0,
            created_at: st.created_at || new Date().toISOString(),
            updated_at: st.updated_at || new Date().toISOString()
          })) as SubtaskResponse[],
          created_at: data.created_at || new Date().toISOString(),
          updated_at: data.updated_at || new Date().toISOString()
        };
        setTask(taskResponse);
        setError('');
      } catch (err) {
        console.error('Error fetching task:', err);
        setError(`Failed to fetch task: ${err instanceof Error ? err.message : String(err)}`);
      } finally {
        setLoading(false);
      }
    };

    // Execute fetch and WebSocket initialization
    let isMounted = true;
    
    fetchInitialTask().then(() => {
      // Only initialize WebSocket if component is still mounted
      if (isMounted) {
        // Initialize WebSocket after fetching initial task data
        try {
          initWebSocket().catch((error) => {
            console.error('Failed to initialize WebSocket:', error);
            // Don't rethrow, just log the error
          });
        } catch (error) {
          console.error('Error during WebSocket initialization:', error);
          // Don't rethrow, just log the error
        }
      }
    }).catch(error => {
      console.error('Error in initial task fetch chain:', error);
      // Don't rethrow, just log the error
    });

    // Cleanup function
    return () => {
      isMounted = false;
      console.log('Cleaning up WebSocket connection');

      // Close WebSocket connection if it exists
      if (ws.current) {
        try {
          // Remove all event listeners first to prevent memory leaks
          ws.current.onopen = null;
          ws.current.onmessage = null;
          ws.current.onerror = null;
          ws.current.onclose = null;

          // Only close if not already in closing/closed state
          if (ws.current.readyState === WebSocket.OPEN) {
            ws.current.close(1000, 'Component unmounting');
          }
          ws.current = null;
        } catch (error) {
          console.error('Error during WebSocket cleanup:', error);
        }
      }

      // Clear any pending reconnection attempts
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
        reconnectTimeout.current = null;
      }

      // Reset reconnection attempts counter
      reconnectAttempts.current = 0;
    };
  }, [taskId, initWebSocket]);

  // Helper function to get status class based on task status
  const getStatusClass = (status: string): string => {
    switch (status.toUpperCase()) {
      case 'COMPLETED':
        return 'bg-green-100 text-green-800';
      case 'IN_PROGRESS':
        return 'bg-blue-100 text-blue-800';
      case 'FAILED':
        return 'bg-red-100 text-red-800';
      case 'PENDING':
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Render the task status with modern styling
  return (
    <div className={`${darkMode ? 'bg-gray-800 text-white' : 'bg-white text-gray-800'} shadow-md rounded-lg p-6 mb-6`}>
      {loading ? (
        <div className="flex justify-center items-center h-40">
          <div className={`animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 ${darkMode ? 'border-blue-400' : 'border-blue-500'}`}></div>
        </div>
      ) : error ? (
        <div className="error-container">
          <div className={`${darkMode ? 'bg-red-900 text-red-300' : 'bg-red-50 text-red-600'} p-4 rounded-md mb-4`}>
            {error}
            {connectionStatus === 'disconnected' && (
              <button 
                onClick={() => {
                  setError('');
                  setIsReconnecting(true);
                  initWebSocket().catch(() => {
                    setIsReconnecting(false);
                  });
                }}
                disabled={isReconnecting}
                className={`px-4 py-2 ${darkMode ? 'bg-blue-600 hover:bg-blue-700' : 'bg-blue-500 hover:bg-blue-600'} text-white rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed mt-3`}
              >
                {isReconnecting ? 'Reconnecting...' : 'Reconnect'}
              </button>
            )}
          </div>
        </div>
      ) : !task ? (
        <div className={`${darkMode ? 'bg-yellow-900 text-yellow-300' : 'bg-yellow-50 text-yellow-600'} p-4 rounded-md`}>
          No task data available
        </div>
      ) : (
        <div className="task-details">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">
              Task: {task.task_id}
            </h2>
            <div className="connection-status-indicator">
              {connectionStatus === 'connected' && (
                <span className="flex items-center text-green-500">
                  <span className="w-2 h-2 bg-green-500 rounded-full mr-1"></span>
                  Connected
                </span>
              )}
              {connectionStatus === 'connecting' && (
                <span className="flex items-center text-yellow-500">
                  <span className="w-2 h-2 bg-yellow-500 rounded-full mr-1"></span>
                  Connecting...
                </span>
              )}
              {connectionStatus === 'disconnected' && (
                <span className="flex items-center text-red-500">
                  <span className="w-2 h-2 bg-red-500 rounded-full mr-1"></span>
                  Disconnected
                </span>
              )}
            </div>
          </div>
          
          <div className="task-info mb-6">
            <div className="grid grid-cols-2 gap-4">
              <div className={`${darkMode ? 'bg-gray-700' : 'bg-gray-100'} p-3 rounded-md`}>
                <span className="text-sm opacity-70">Status</span>
                <p className="font-medium">{task.status}</p>
              </div>
              <div className={`${darkMode ? 'bg-gray-700' : 'bg-gray-100'} p-3 rounded-md`}>
                <span className="text-sm opacity-70">Progress</span>
                <p className="font-medium">{task.progress}%</p>
              </div>
            </div>
            {task.error && (
              <div className={`mt-4 ${darkMode ? 'bg-red-900 text-red-300' : 'bg-red-50 text-red-600'} p-3 rounded-md`}>
                <span className="font-medium">Error:</span> {task.error}
              </div>
            )}
          </div>
          
          <div className="subtasks mb-6">
            <h3 className="text-lg font-medium mb-3">Subtasks</h3>
            {task.subtasks && task.subtasks.length > 0 ? (
              <div className="space-y-3">
                {task.subtasks.map((subtask: SubtaskResponse) => (
                  <div key={subtask.id} className={`${darkMode ? 'bg-gray-700' : 'bg-gray-100'} p-4 rounded-md`}>
                    <div className="flex justify-between mb-2">
                      <span className="font-medium">{subtask.type}</span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusClass(subtask.status)}`}>
                        {subtask.status}
                      </span>
                    </div>
                    <div className="w-full bg-gray-300 rounded-full h-2.5 mb-3">
                      <div 
                        className="bg-blue-500 h-2.5 rounded-full" 
                        style={{ width: `${subtask.progress}%` }}
                      ></div>
                    </div>
                    {subtask.error && (
                      <div className={`mt-2 ${darkMode ? 'bg-red-900 text-red-300' : 'bg-red-50 text-red-600'} p-2 rounded-md text-sm`}>
                        <span className="font-medium">Error:</span> {subtask.error}
                      </div>
                    )}
                    {subtask.result && (
                      <div className="mt-2 text-sm">
                        <span className="font-medium">Result:</span> {subtask.result}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No subtasks available</p>
            )}
          </div>
          
          {task.result && (
            <div className="task-result mb-6">
              <h3 className="text-lg font-medium mb-3">Result</h3>
              <div className={`${darkMode ? 'bg-gray-700' : 'bg-gray-100'} p-4 rounded-md`}>
                <pre className="whitespace-pre-wrap">{task.result}</pre>
              </div>
            </div>
          )}
          
          {connectionStatus === 'disconnected' && (
            <div className="flex justify-center mt-6">
              <button 
                onClick={() => {
                  setIsReconnecting(true);
                  initWebSocket().catch(() => {
                    setIsReconnecting(false);
                  });
                }}
                disabled={isReconnecting}
                className={`px-4 py-2 ${darkMode ? 'bg-blue-600 hover:bg-blue-700' : 'bg-blue-500 hover:bg-blue-600'} text-white rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {isReconnecting ? 'Reconnecting...' : 'Reconnect to WebSocket'}
              </button>
            </div>
          )}
        </div>
      )}
      <div className="mt-6 text-center">
        <button
          onClick={() => router.push('/')}
          className={`py-2 px-4 ${darkMode ? 'bg-gray-600 hover:bg-gray-700' : 'bg-blue-600 hover:bg-blue-700'} text-white font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-opacity-50`}
        >
          Back to Task List
        </button>
      </div>
    </div>
  );
};

export default TaskStatus;
