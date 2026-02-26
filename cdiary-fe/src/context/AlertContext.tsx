import React, { createContext, useContext, useState, ReactNode } from 'react';
import { CustomAlert } from '../components/common/CustomAlert';

interface AlertContextType {
  showAlert: (message: string, title?: string) => void;
  showConfirm: (message: string, title?: string) => Promise<boolean>;
}

const AlertContext = createContext<AlertContextType | undefined>(undefined);

export const AlertProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [alertState, setAlertState] = useState<{
    isOpen: boolean;
    message: string;
    title?: string;
    type: 'alert' | 'confirm';
    resolve?: (value: boolean) => void;
  }>({
    isOpen: false,
    message: '',
    type: 'alert'
  });

  const showAlert = (message: string, title?: string) => {
    setAlertState({
      isOpen: true,
      message,
      title,
      type: 'alert'
    });
  };

  const showConfirm = (message: string, title?: string): Promise<boolean> => {
    return new Promise((resolve) => {
      setAlertState({
        isOpen: true,
        message,
        title,
        type: 'confirm',
        resolve
      });
    });
  };

  const handleConfirm = () => {
    if (alertState.resolve) {
      alertState.resolve(true);
    }
    setAlertState(prev => ({ ...prev, isOpen: false }));
  };

  const handleCancel = () => {
    if (alertState.resolve) {
      alertState.resolve(false);
    }
    setAlertState(prev => ({ ...prev, isOpen: false }));
  };

  return (
    <AlertContext.Provider value={{ showAlert, showConfirm }}>
      {children}
      <CustomAlert
        isOpen={alertState.isOpen}
        message={alertState.message}
        title={alertState.title}
        type={alertState.type}
        onConfirm={handleConfirm}
        onCancel={handleCancel}
      />
    </AlertContext.Provider>
  );
};

export const useAlert = () => {
  const context = useContext(AlertContext);
  if (!context) {
    throw new Error('useAlert must be used within an AlertProvider');
  }
  return context;
};
