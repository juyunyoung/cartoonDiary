import React, { ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

interface TopBarProps {
  title?: string;
  showBack?: boolean;
  onBack?: () => void;
  leftAction?: ReactNode;
  rightAction?: ReactNode;
}

export const TopBar: React.FC<TopBarProps> = ({ title, showBack = false, onBack, leftAction, rightAction }) => {
  const navigate = useNavigate();

  const handleBack = () => {
    if (onBack) onBack();
    else navigate(-1);
  };

  return (
    <header className="h-14 flex items-center px-4 border-b border-primary/10 sticky top-0 bg-white/80 backdrop-blur-sm z-10">
      <div className="min-w-[40px] flex justify-start">
        {showBack ? (
          <button onClick={handleBack} className="p-2 -ml-2 rounded-full hover:bg-secondary/20 transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </button>
        ) : leftAction}
      </div>
      <h1 className="flex-1 text-center font-bold text-lg truncate px-2">{title}</h1>
      <div className="min-w-[40px] flex justify-end">
        {rightAction}
      </div>
    </header>
  );
};
