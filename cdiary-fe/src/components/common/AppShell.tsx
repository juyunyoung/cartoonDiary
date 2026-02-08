import React from 'react';

export const AppShell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-md mx-auto min-h-screen bg-background shadow-xl overflow-hidden flex flex-col">
        {children}
      </div>
    </div>
  );
};
