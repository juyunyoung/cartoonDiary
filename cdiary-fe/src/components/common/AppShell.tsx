import React from 'react';

export const AppShell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <div className="max-w-md mx-auto min-h-screen bg-white dark:bg-gray-800 shadow-xl overflow-hidden flex flex-col">
        {children}
      </div>
    </div>
  );
};
