import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export const useAuth = () => {
  const navigate = useNavigate();
  const userId = localStorage.getItem('userId');

  useEffect(() => {
    if (!userId) {
      navigate('/signin', { replace: true });
    }
  }, [userId, navigate]);

  return { userId };
};
