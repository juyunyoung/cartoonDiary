import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AppShell } from '../components/common/AppShell';

export const LoginScreen: React.FC = () => {
  const navigate = useNavigate();

  const handleLogin = () => {
    // Mock login logic
    // In a real app, this would handle authentication
    console.log("Logging in...");
    navigate('/home');
  };

  return (
    <AppShell>
      <div className="flex flex-col items-center justify-center min-h-[80vh] px-6 text-center">
        {/* Logo or Iconic Image */}
        <div className="w-32 h-32 bg-primary/20 rounded-full flex items-center justify-center mb-8">
          <span className="text-4xl">📒</span>
        </div>

        <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-2">
          Cartoon Diary
        </h1>
        <p className="text-gray-500 dark:text-gray-400 mb-12">
          Turn your daily moments into a comic strip.
        </p>

        <div className="w-full max-w-xs space-y-3">
          <button
            onClick={() => navigate('/signup')}
            className="w-full bg-primary hover:bg-primary/90 text-white font-bold py-3 px-4 rounded-xl shadow-lg transition-transform active:scale-95"
          >
            Sign Up
          </button>

          <button
            onClick={() => navigate('/signin')}
            className="w-full bg-white border border-gray-300 text-gray-700 font-bold py-3 px-4 rounded-xl shadow-sm hover:bg-gray-50 transition-colors"
          >
            Login
          </button>

          <div className="relative flex items-center py-2">
            <div className="flex-grow border-t border-gray-300"></div>
            <span className="flex-shrink-0 mx-4 text-gray-400 text-xs">OR</span>
            <div className="flex-grow border-t border-gray-300"></div>
          </div>

          <button
            onClick={handleLogin}
            className="w-full bg-white border border-gray-300 text-gray-700 font-medium py-3 px-4 rounded-xl shadow-sm hover:bg-gray-50 flex items-center justify-center gap-3 transition-colors"
          >
            <img
              src="https://www.google.com/favicon.ico"
              alt="Google"
              className="w-5 h-5"
            />
            Sign in with Google
          </button>
        </div>

        <p className="mt-8 text-xs text-gray-400">
          By signing in, you agree to our Terms of Service and Privacy Policy.
        </p>
      </div>
    </AppShell>
  );
};
