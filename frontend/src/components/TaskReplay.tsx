'use client';

import { useState, useEffect, useRef } from 'react';
import { FiPlay, FiPause, FiSkipBack, FiSkipForward, FiClock, FiX } from 'react-icons/fi';
import { getTaskReplay } from '@/services/api';
import { useTheme } from '@/context/ThemeContext';

interface TaskReplayProps {
  taskId: string;
  onClose?: () => void;
}

interface LogEntry {
  timestamp: string;
  subtask_id?: string;
  subtask_type?: string;
  action: string;
  details?: string;
}

interface ReplayData {
  task: any;
  logs: LogEntry[];
  speed: number;
  duration: number;
}

export default function TaskReplay({ taskId, onClose }: TaskReplayProps) {
  const { darkMode } = useTheme();
  const [replayData, setReplayData] = useState<ReplayData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentLogIndex, setCurrentLogIndex] = useState(-1);
  const [speed, setSpeed] = useState(1.0);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [taskState, setTaskState] = useState<any>(null);
  const [visibleLogs, setVisibleLogs] = useState<LogEntry[]>([]);
  
  const socket = useRef<WebSocket | null>(null);
  const animationRef = useRef<number | null>(null);
  const lastTimestampRef = useRef<number | null>(null);
  
  // Load replay data
  useEffect(() => {
    const fetchReplayData = async () => {
      try {
        setLoading(true);
        const data = await getTaskReplay(taskId, speed);
        setReplayData(data.replay);
        setDuration(data.replay.duration);
        setTaskState(data.replay.task);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching replay data:', err);
        setError('Failed to load replay data');
        setLoading(false);
      }
    };
    
    fetchReplayData();
    
    return () => {
      // Cleanup
      if (socket.current) {
        socket.current.close();
      }
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [taskId, speed]);
  
  // Handle WebSocket connection for real-time replay
  useEffect(() => {
    if (!replayData || !isPlaying) return;
    
    const connectWebSocket = () => {
      // Connect to the backend server on port 8098
      const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//localhost:8098/ws/${taskId}/replay`;
      socket.current = new WebSocket(wsUrl);
      
      socket.current.onopen = () => {
        // Send initial settings
        socket.current?.send(JSON.stringify({ speed }));
      };
      
      socket.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'task_initial') {
          setTaskState(data.data);
        } else if (data.type === 'log_entry') {
          const newLog = data.data as LogEntry;
          setVisibleLogs(prev => [...prev, newLog]);
          setCurrentLogIndex(prev => prev + 1);
        } else if (data.type === 'replay_complete') {
          setIsPlaying(false);
        } else if (data.error) {
          setError(data.error);
          setIsPlaying(false);
        }
      };
      
      socket.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('WebSocket connection error');
        setIsPlaying(false);
      };
      
      socket.current.onclose = () => {
        console.log('WebSocket connection closed');
      };
    };
    
    connectWebSocket();
    
    return () => {
      if (socket.current) {
        socket.current.close();
      }
    };
  }, [replayData, isPlaying, taskId, speed]);
  
  // Handle animation frame for local replay
  const animate = (timestamp: number) => {
    if (!lastTimestampRef.current) {
      lastTimestampRef.current = timestamp;
    }
    
    const elapsed = timestamp - lastTimestampRef.current;
    
    if (elapsed > 1000 / speed) {
      lastTimestampRef.current = timestamp;
      
      if (replayData && currentLogIndex < replayData.logs.length - 1) {
        const nextIndex = currentLogIndex + 1;
        setCurrentLogIndex(nextIndex);
        setVisibleLogs(replayData.logs.slice(0, nextIndex + 1));
        
        // Update current time based on log timestamps
        if (replayData.logs[0] && replayData.logs[nextIndex]) {
          const startTime = new Date(replayData.logs[0].timestamp).getTime();
          const currentLogTime = new Date(replayData.logs[nextIndex].timestamp).getTime();
          const elapsedSeconds = (currentLogTime - startTime) / 1000;
          setCurrentTime(elapsedSeconds);
        }
      } else {
        // End of replay
        setIsPlaying(false);
        return;
      }
    }
    
    if (isPlaying) {
      animationRef.current = requestAnimationFrame(animate);
    }
  };
  
  // Handle play/pause
  useEffect(() => {
    if (isPlaying && replayData) {
      // Start animation
      lastTimestampRef.current = null;
      animationRef.current = requestAnimationFrame(animate);
    } else if (animationRef.current) {
      // Stop animation
      cancelAnimationFrame(animationRef.current);
    }
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isPlaying, replayData, currentLogIndex, speed]);
  
  const handlePlay = () => {
    setIsPlaying(true);
    // If we have a WebSocket connection, send a resume command
    if (socket.current && socket.current.readyState === WebSocket.OPEN) {
      socket.current.send(JSON.stringify({ action: 'resume' }));
    }
  };
  
  const handlePause = () => {
    setIsPlaying(false);
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }
    // If we have a WebSocket connection, send a pause command
    if (socket.current && socket.current.readyState === WebSocket.OPEN) {
      socket.current.send(JSON.stringify({ action: 'pause' }));
    }
  };
  
  const handleRestart = () => {
    setIsPlaying(false);
    setCurrentLogIndex(-1);
    setVisibleLogs([]);
    setCurrentTime(0);
    
    // Close and reopen socket if needed
    if (socket.current) {
      socket.current.close();
      socket.current = null;
    }
  };
  
  const handleSpeedChange = (newSpeed: number) => {
    setSpeed(newSpeed);
    // If we have a WebSocket connection, send a speed change command
    if (socket.current && socket.current.readyState === WebSocket.OPEN) {
      socket.current.send(JSON.stringify({ action: 'set_speed', speed: newSpeed }));
    }
  };
  
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };
  
  // Render subtask status based on visible logs
  const renderSubtaskStatus = () => {
    if (!taskState || !taskState.subtasks) return null;
    
    return (
      <div className={`mt-4 ${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg p-4`}>
        <h3 className={`text-lg font-medium mb-2 ${darkMode ? 'text-gray-200' : 'text-gray-800'}`}>Subtasks</h3>
        <div className="space-y-2">
          {taskState.subtasks.map((subtask: any) => {
            // Find the latest log for this subtask
            const subtaskLogs = visibleLogs.filter(log => log.subtask_id === subtask.id);
            const latestLog = subtaskLogs.length > 0 ? subtaskLogs[subtaskLogs.length - 1] : null;
            
            let statusColor = darkMode ? 'bg-gray-700' : 'bg-gray-200';
            if (latestLog) {
              if (latestLog.action === 'completed' || latestLog.action === 'container_completed') {
                statusColor = darkMode ? 'bg-green-700' : 'bg-green-200';
              } else if (latestLog.action === 'failed' || latestLog.action === 'container_failed') {
                statusColor = darkMode ? 'bg-red-700' : 'bg-red-200';
              } else if (latestLog.action === 'started' || latestLog.action === 'container_started') {
                statusColor = darkMode ? 'bg-blue-700' : 'bg-blue-200';
              }
            }
            
            return (
              <div 
                key={subtask.id} 
                className={`${darkMode ? 'bg-gray-700' : 'bg-gray-100'} rounded p-2 flex items-center`}
              >
                <div className={`w-3 h-3 rounded-full ${statusColor} mr-2`}></div>
                <div className="flex-1">
                  <div className={`text-sm font-medium ${darkMode ? 'text-gray-200' : 'text-gray-800'}`}>
                    {subtask.type.replace('_', ' ').charAt(0).toUpperCase() + subtask.type.replace('_', ' ').slice(1)}
                  </div>
                  {subtask.description && (
                    <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                      {subtask.description}
                    </div>
                  )}
                </div>
                {latestLog && (
                  <div className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                    {latestLog.action.replace('_', ' ')}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };
  
  if (loading) {
    return (
      <div className={`p-6 ${darkMode ? 'bg-gray-900 text-gray-100' : 'bg-white text-gray-900'} rounded-xl shadow-lg`}>
        <div className="flex justify-center items-center h-40">
          <div className={`animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 ${darkMode ? 'border-gray-200' : 'border-gray-800'}`}></div>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className={`p-6 ${darkMode ? 'bg-gray-900 text-gray-100' : 'bg-white text-gray-900'} rounded-xl shadow-lg`}>
        <div className={`${darkMode ? 'bg-red-900 text-red-200' : 'bg-red-100 text-red-800'} p-4 rounded-lg`}>
          <p>Error: {error}</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className={`p-6 ${darkMode ? 'bg-gray-900 text-gray-100' : 'bg-white text-gray-900'} rounded-xl shadow-lg`}>
      <div className="flex justify-between items-center mb-4">
        <h2 className={`text-xl font-semibold ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>
          Task Execution Replay
        </h2>
        {onClose && (
          <button
            onClick={onClose}
            className={`p-2 rounded-full ${darkMode ? 'hover:bg-gray-800' : 'hover:bg-gray-100'} transition-colors`}
          >
            <FiX className={`w-5 h-5 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`} />
          </button>
        )}
      </div>
      
      {/* Playback controls */}
      <div className={`${darkMode ? 'bg-gray-800' : 'bg-gray-100'} rounded-lg p-3 flex items-center justify-between mb-4`}>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleRestart}
            className={`p-2 rounded-full ${darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-200'} transition-colors`}
            title="Restart"
          >
            <FiSkipBack className={`w-5 h-5 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`} />
          </button>
          
          {isPlaying ? (
            <button
              onClick={handlePause}
              className={`p-2 rounded-full ${darkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-white hover:bg-gray-200'} transition-colors`}
              title="Pause"
            >
              <FiPause className={`w-5 h-5 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`} />
            </button>
          ) : (
            <button
              onClick={handlePlay}
              className={`p-2 rounded-full ${darkMode ? 'bg-orange-600 hover:bg-orange-700' : 'bg-blue-600 hover:bg-blue-700'} transition-colors`}
              title="Play"
            >
              <FiPlay className="w-5 h-5 text-white" />
            </button>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          <FiClock className={`w-4 h-4 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`} />
          <span className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>
        </div>
        
        <div className="flex items-center space-x-2">
          <span className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Speed:</span>
          <select
            value={speed}
            onChange={(e) => handleSpeedChange(parseFloat(e.target.value))}
            className={`${darkMode ? 'bg-gray-700 text-gray-300' : 'bg-white text-gray-800'} rounded px-2 py-1 text-sm`}
          >
            <option value="0.5">0.5x</option>
            <option value="1">1x</option>
            <option value="2">2x</option>
            <option value="5">5x</option>
          </select>
        </div>
      </div>
      
      {/* Subtask status visualization */}
      {renderSubtaskStatus()}
      
      {/* Execution log */}
      <div className="mt-4">
        <h3 className={`text-lg font-medium mb-2 ${darkMode ? 'text-gray-200' : 'text-gray-800'}`}>Execution Log</h3>
        <div 
          className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg p-4 max-h-80 overflow-y-auto font-mono text-sm`}
        >
          {visibleLogs.length === 0 ? (
            <div className={`${darkMode ? 'text-gray-400' : 'text-gray-500'} italic`}>
              No logs to display. Press play to start the replay.
            </div>
          ) : (
            <div className="space-y-2">
              {visibleLogs.map((log, index) => {
                let actionColor = '';
                if (log.action === 'completed' || log.action === 'container_completed' || log.action === 'task_completed') {
                  actionColor = darkMode ? 'text-green-400' : 'text-green-600';
                } else if (log.action === 'failed' || log.action === 'container_failed' || log.action === 'task_failed') {
                  actionColor = darkMode ? 'text-red-400' : 'text-red-600';
                } else if (log.action === 'started' || log.action === 'container_started') {
                  actionColor = darkMode ? 'text-blue-400' : 'text-blue-600';
                }
                
                return (
                  <div key={index} className="flex">
                    <div className={`w-24 flex-shrink-0 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </div>
                    <div className={`w-32 flex-shrink-0 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                      {log.subtask_type ? log.subtask_type.replace('_', ' ') : 'system'}
                    </div>
                    <div className={`w-24 flex-shrink-0 ${actionColor}`}>
                      {log.action.replace('_', ' ')}
                    </div>
                    <div className={`flex-1 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                      {log.details || ''}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
