import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppShell } from '../components/common/AppShell';
import { TopBar } from '../components/common/TopBar';
import { api } from '../api/client';
import { useLanguage } from '../context/LanguageContext';

export const SignInScreen: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [error, setError] = useState('');
  const { t } = useLanguage();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await api.login({
        username: formData.username,
        password: formData.password
      });

      localStorage.setItem('token', response.access_token);
      localStorage.setItem('userId', response.user_id);

      navigate('/home');
    } catch (err: any) {
      setError(err.message || t('invalid_auth'));
    }
  };

  return (
    <AppShell>
      <TopBar title={t('sign_in_title')} showBack={true} />
      <div className="p-6 flex flex-col justify-center min-h-[60vh]">
        <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">{t('welcome_back')}</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">{t('username')}</label>
            <input
              type="text"
              name="username"
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary focus:border-primary"
              value={formData.username}
              onChange={handleChange}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">{t('password')}</label>
            <input
              type="password"
              name="password"
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary focus:border-primary"
              value={formData.password}
              onChange={handleChange}
            />
          </div>

          {error && <p className="text-red-500 text-sm">{error}</p>}

          <button
            type="submit"
            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary mt-4"
          >
            {t('sign_in_title')}
          </button>
          <p className="mt-8 text-center text-sm text-gray-500">
            {t('no_account')}{' '}
            <button
              onClick={() => navigate('/signup')}
              className="text-primary font-bold hover:underline"
            >
              {t('sign_up_title')}
            </button>
          </p>
        </form>
      </div>
    </AppShell>
  );
};
