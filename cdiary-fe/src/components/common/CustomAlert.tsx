import React from 'react';
import { useLanguage } from '../../context/LanguageContext';

interface CustomAlertProps {
  isOpen: boolean;
  title?: string;
  message: string;
  type?: 'alert' | 'confirm';
  onConfirm: () => void;
  onCancel?: () => void;
}

export const CustomAlert: React.FC<CustomAlertProps> = ({
  isOpen,
  title,
  message,
  type = 'alert',
  onConfirm,
  onCancel
}) => {
  const { t } = useLanguage();
  if (!isOpen) return null;

  const displayTitle = title || t('ok'); // Fallback if no title provided

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white dark:bg-gray-900 rounded-3xl shadow-2xl w-full max-w-sm overflow-hidden animate-in zoom-in-95 duration-200 border border-primary/20">
        <div className="p-6 text-center">
          {displayTitle && (
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
              {displayTitle}
            </h3>
          )}
          <p className="text-gray-600 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">
            {message}
          </p>
        </div>

        <div className="flex border-t border-gray-100 dark:border-gray-800">
          {type === 'confirm' && (
            <button
              onClick={onCancel}
              className="flex-1 px-4 py-4 text-gray-500 font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors border-r border-gray-100 dark:border-gray-800"
            >
              {t('cancel')}
            </button>
          )}
          <button
            onClick={onConfirm}
            className="flex-1 px-4 py-4 text-primary font-bold hover:bg-primary/5 transition-colors"
          >
            {t('ok')}
          </button>
        </div>
      </div>
    </div>
  );
};
