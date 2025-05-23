// Task types for the Autonomous AI Agent frontend

/**
 * Task status enum
 */
export enum TaskStatus {
  PENDING = 'PENDING',
  IN_PROGRESS = 'IN_PROGRESS',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED'
}

/**
 * Subtask interface
 */
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

/**
 * Task interface
 */
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

/**
 * Task submission request
 */
export interface TaskSubmitRequest {
  task: string;
  context?: Record<string, any>;
}

/**
 * Task response from the API
 */
export interface TaskResponse extends Task {
  // Additional fields that might be returned by the API
}

/**
 * Task log entry
 */
export interface TaskLogEntry {
  timestamp: string;
  subtask_id: string;
  subtask_type: string;
  action: string;
  details: string;
}
