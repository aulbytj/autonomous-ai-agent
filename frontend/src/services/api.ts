// API service for interacting with the Autonomous AI Agent backend
import axios, { AxiosError } from 'axios';
import config from '../config/environment';

// Re-export task types to avoid import errors
export enum TaskStatus {
  PENDING = 'PENDING',
  IN_PROGRESS = 'IN_PROGRESS',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED'
}

export interface Subtask {
  id: string;
  type: string;
  description: string;
  status: TaskStatus;
  dependencies: string[];
  result?: any;
  error?: string;
  created_at: string;
  updated_at: string;
}

export interface Task {
  task_id: string;
  status: TaskStatus;
  progress: number;
  subtasks: Subtask[];
  result?: any;
  error?: string;
  created_at?: string;
  updated_at?: string;
}

export interface TaskSubmitRequest {
  task: string;
  context?: { [key: string]: any; priority?: number };
}

const API_BASE_URL = config.apiBaseUrl;
const WS_BASE_URL = config.wsBaseUrl;

// Error types for better handling
export enum ErrorType {
  SERVER_ERROR = 'SERVER_ERROR',
  NETWORK_ERROR = 'NETWORK_ERROR',
  REDIS_UNAVAILABLE = 'REDIS_UNAVAILABLE',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  UNKNOWN_ERROR = 'UNKNOWN_ERROR'
}

// Structured error response
export interface ApiErrorResponse {
  message: string;
  type: ErrorType;
  statusCode?: number;
  retryable: boolean;
}

// Error handling utility
const handleApiError = (error: unknown, defaultMessage: string): ApiErrorResponse => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError;
    if (axiosError.response) {
      // Server responded with an error status
      const data = axiosError.response.data as any;
      const statusCode = axiosError.response.status;
      
      // Check for specific error types
      if (statusCode === 503 && (data.detail?.includes('Storage service') || data.detail?.includes('Redis'))) {
        return {
          message: 'Storage service is temporarily unavailable. Some features may be limited.',
          type: ErrorType.REDIS_UNAVAILABLE,
          statusCode,
          retryable: true
        };
      } else if (statusCode === 400) {
        return {
          message: data.detail || 'Invalid request parameters',
          type: ErrorType.VALIDATION_ERROR,
          statusCode,
          retryable: false
        };
      } else if (statusCode >= 500) {
        return {
          message: data.detail || 'Server error occurred. Please try again later.',
          type: ErrorType.SERVER_ERROR,
          statusCode,
          retryable: true
        };
      }
      
      return {
        message: data.detail || data.message || defaultMessage,
        type: ErrorType.UNKNOWN_ERROR,
        statusCode,
        retryable: statusCode < 500
      };
    } else if (axiosError.request) {
      // Request was made but no response received
      return {
        message: 'No response received from server. Please check your connection and try again.',
        type: ErrorType.NETWORK_ERROR,
        retryable: true
      };
    }
  }
  
  // Default error response
  return {
    message: defaultMessage,
    type: ErrorType.UNKNOWN_ERROR,
    retryable: false
  };
};

// Centralized error handling utility
async function handleApiResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text();
    console.error(`API error response (${response.status}):`, errorText);
    
    let errorMessage = '';
    try {
      // Try to parse as JSON
      const errorData = JSON.parse(errorText);
      errorMessage = errorData.detail || `Error: ${response.status}`;
    } catch (e) {
      // If not valid JSON, use the raw text
      errorMessage = `Error ${response.status}: ${errorText || 'Unknown error'}`;
    }
    
    // Create a structured error object instead of throwing a generic Error
    const apiError: ApiErrorResponse = {
      message: errorMessage,
      type: response.status >= 500 ? ErrorType.SERVER_ERROR : ErrorType.UNKNOWN_ERROR,
      statusCode: response.status,
      retryable: response.status >= 500 || response.status === 429
    };
    
    // Log the structured error for debugging
    console.error('Structured API error:', apiError);
    
    // Return a rejected promise with the structured error
    return Promise.reject(apiError);
  }
  
  try {
    // Safely parse the JSON response
    return await response.json() as T;
  } catch (error) {
    console.error('Error parsing JSON response:', error);
    return Promise.reject({
      message: 'Failed to parse API response',
      type: ErrorType.UNKNOWN_ERROR,
      retryable: false
    });
  }
}

/**
 * Check if the API is available
 */
export async function checkApiHealth(): Promise<boolean> {
  try {
    console.log('Checking API health...');
    const response = await fetch(`${API_BASE_URL}/api/health`, { 
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });
    
    if (!response.ok) {
      console.error('API health check failed:', response.status);
      return false;
    }
    
    const data = await response.json();
    console.log('API health check response:', data);
    return data.status === 'ok';
  } catch (error) {
    console.error('API health check error:', error);
    return false;
  }
}

/**
 * Test task submission - for debugging purposes
 */
export async function testTaskSubmission(taskRequest: TaskSubmitRequest): Promise<{ task_id: string }> {
  try {
    console.log('Testing task submission with:', taskRequest);
    const response = await fetch(`${API_BASE_URL}/api/test-submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(taskRequest),
    });

    const data = await handleApiResponse<{ task_id: string }>(response);
    console.log('Test task submission response:', data);
    return { task_id: data.task_id };
  } catch (error) {
    console.error('Error in test task submission:', error);
    throw error;
  }
}

export interface TaskSubmitRequest {
  task: string;
  context?: {
    priority?: number;
    [key: string]: any;
  };
}

export interface TaskResponse {
  task_id: string;
  status: string;
  result: string | null;
  error: string | null;
  progress: number;
  subtasks: SubtaskResponse[];
  created_at: string;
  updated_at: string;
}

export interface SubtaskResponse {
  id: string;
  type: string;
  status: string;
  result: string | null;
  error: string | null;
  progress: number;
  created_at: string;
  updated_at: string;
}

/**
 * Submit a new task to the Autonomous AI Agent
 */
export async function submitTask(taskRequest: TaskSubmitRequest): Promise<{ task_id: string }> {
  try {
    console.log('Submitting task:', taskRequest);
    const response = await axios.post(`${API_BASE_URL}/tasks/submit`, {
      task: taskRequest.task,
      context: taskRequest.context
    });
    return response.data;
  } catch (error) {
    const errorResponse = handleApiError(error, 'Failed to submit task');
    console.error('Task submission error:', errorResponse);
    throw errorResponse;
  }
}

/**
 * Get the status of a task by its ID
 */
export async function getTaskStatus(taskId: string): Promise<Task> {
  try {
    console.log('Fetching task status for:', taskId);
    const response = await axios.get(`${API_BASE_URL}/tasks/${taskId}`);
    return response.data;
  } catch (error) {
    const errorResponse = handleApiError(error, 'Failed to get task status');
    console.error('Task status error:', errorResponse);
    throw errorResponse;
  }
}

/**
 * Get task history
 * This replaces the previous getRedisKeys function which used a test endpoint
 */
export async function getTaskHistory(): Promise<{ tasks?: string[], keys?: string[], status?: string, error?: string, errorDetails?: ApiErrorResponse }> {
  try {
    // Use the correct API endpoint path - match the exact endpoint in the backend
    const endpoint = `${API_BASE_URL}/test/redis-keys`;
    console.log('Fetching task history from:', endpoint);
    
    // Safely handle potential network errors
    let response;
    try {
      response = await fetch(endpoint);
    } catch (networkError) {
      console.error('Network error fetching task history:', networkError);
      // Return a default empty response instead of throwing
      return { tasks: [] };
    }

    // Process the response with our improved error handler
    try {
      const data = await handleApiResponse<{ status: string; keys: string[] }>(response);
      console.log('Task history response:', data);
      return data;
    } catch (err) {
      console.error('Error handling API response:', err);
      // Return a structured error that won't cause unhandled exceptions
      return { 
        keys: [],
        status: 'error',
        error: err instanceof Error ? err.message : 'Unknown error in response handling'
      };
    }
  } catch (error) {
    // Log the error but don't rethrow
    console.error('Error fetching task history:', error);
    
    // Create a structured error message for the UI
    let errorMessage = 'Failed to fetch task history';
    if ((error as ApiErrorResponse)?.message) {
      errorMessage += `: ${(error as ApiErrorResponse).message}`;
    } else if (error instanceof Error) {
      errorMessage += `: ${error.message}`;
    }
    
    // Instead of throwing, return an object with error information
    // This prevents unhandled promise rejections
    return { 
      tasks: [],
      error: errorMessage,
      errorDetails: error as ApiErrorResponse
    } as any;
  }
}

/**
 * Delete a task by its ID
 */
export async function deleteTask(taskId: string): Promise<{ status: string; message: string }> {
  try {
    console.log('Deleting task:', taskId);
    const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
      method: 'DELETE',
    });

    const data = await handleApiResponse<{ status: string; message: string }>(response);
    console.log('Task deletion response:', data);
    return data;
  } catch (error) {
    console.error('Error deleting task:', error);
    throw error;
  }
}

/**
 * Get the execution logs for a task
 */
export async function getTaskLogs(taskId: string): Promise<{ logs: any[] }> {
  try {
    console.log('Fetching task logs for:', taskId);
    const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/logs`);

    const data = await handleApiResponse<{ logs: any[] }>(response);
    console.log('Task logs response:', data);
    return data;
  } catch (error) {
    console.error('Error fetching task logs:', error);
    throw error;
  }
}

/**
 * Get replay data for a task execution
 */
export async function getTaskReplay(taskId: string, speed: number = 1.0): Promise<{ replay: any }> {
  try {
    console.log('Fetching task replay for:', taskId, 'with speed:', speed);
    const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/replay?speed=${speed}`);

    const data = await handleApiResponse<{ replay: any }>(response);
    console.log('Task replay response:', data);
    return data;
  } catch (error) {
    console.error('Error fetching task replay:', error);
    throw error;
  }
}
