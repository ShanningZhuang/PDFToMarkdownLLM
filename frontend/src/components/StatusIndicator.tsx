'use client';

import React from 'react';
import { CheckCircle, XCircle, AlertCircle, Clock, Loader2, Zap } from 'lucide-react';

export type StatusType = 'idle' | 'processing' | 'success' | 'error' | 'warning' | 'streaming';

interface StatusIndicatorProps {
  status: StatusType;
  message: string;
  details?: string;
  progress?: number;
  showIcon?: boolean;
  className?: string;
}

interface StatusConfig {
  icon: any;
  bgColor: string;
  textColor: string;
  iconColor: string;
  animate?: string;
}

const statusConfig: Record<StatusType, StatusConfig> = {
  idle: {
    icon: Clock,
    bgColor: 'bg-gray-100',
    textColor: 'text-gray-800',
    iconColor: 'text-gray-500',
  },
  processing: {
    icon: Loader2,
    bgColor: 'bg-blue-100',
    textColor: 'text-blue-800',
    iconColor: 'text-blue-500',
    animate: 'animate-spin',
  },
  streaming: {
    icon: Zap,
    bgColor: 'bg-green-100',
    textColor: 'text-green-800',
    iconColor: 'text-green-500',
    animate: 'animate-pulse',
  },
  success: {
    icon: CheckCircle,
    bgColor: 'bg-green-100',
    textColor: 'text-green-800',
    iconColor: 'text-green-500',
  },
  error: {
    icon: XCircle,
    bgColor: 'bg-red-100',
    textColor: 'text-red-800',
    iconColor: 'text-red-500',
  },
  warning: {
    icon: AlertCircle,
    bgColor: 'bg-yellow-100',
    textColor: 'text-yellow-800',
    iconColor: 'text-yellow-500',
  },
};

export default function StatusIndicator({
  status,
  message,
  details,
  progress,
  showIcon = true,
  className = '',
}: StatusIndicatorProps) {
  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <div className={`rounded-lg p-4 ${config.bgColor} ${className}`}>
      <div className="flex items-start space-x-3">
        {showIcon && (
          <Icon 
            className={`h-5 w-5 mt-0.5 ${config.iconColor} ${config.animate || ''}`} 
          />
        )}
        <div className="flex-1 min-w-0">
          <p className={`text-sm font-medium ${config.textColor}`}>
            {message}
          </p>
          {details && (
            <p className={`text-xs mt-1 ${config.textColor} opacity-75`}>
              {details}
            </p>
          )}
          {progress !== undefined && (
            <div className="mt-2">
              <div className="flex items-center justify-between text-xs mb-1">
                <span className={config.textColor}>Progress</span>
                <span className={config.textColor}>{Math.round(progress)}%</span>
              </div>
              <div className="w-full bg-white bg-opacity-50 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${
                    status === 'error' ? 'bg-red-500' : 
                    status === 'success' ? 'bg-green-500' : 
                    'bg-blue-500'
                  }`}
                  style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 