import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { HomeScreen } from './pages/HomeScreen';
import { UserProfileScreen } from './pages/UserProfileScreen';
import { LoginScreen } from './pages/LoginScreen';
import { CharacterCreationScreen } from './pages/CharacterCreationScreen';
import { WriteDiaryScreen } from './pages/WriteDiaryScreen';
import { GeneratingScreen } from './pages/GeneratingScreen';
import { ResultScreen } from './pages/ResultScreen';
import { RegenerateScreen } from './pages/RegenerateScreen';
import { ShareScreen } from './pages/ShareScreen';

import { SignUpScreen } from './pages/SignUpScreen';
import { SignInScreen } from './pages/SignInScreen';
import { ProtectedRoute } from './components/common/ProtectedRoute';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={localStorage.getItem('token') ? <Navigate to="/home" replace /> : <LoginScreen />} />
        <Route path="/signup" element={<SignUpScreen />} />
        <Route path="/signin" element={<SignInScreen />} />

        {/* Protected Routes */}
        <Route path="/home" element={<ProtectedRoute><HomeScreen /></ProtectedRoute>} />
        <Route path="/profile" element={<ProtectedRoute><UserProfileScreen /></ProtectedRoute>} />
        <Route path="/character-create" element={<ProtectedRoute><CharacterCreationScreen /></ProtectedRoute>} />
        <Route path="/write" element={<ProtectedRoute><WriteDiaryScreen /></ProtectedRoute>} />
        <Route path="/generate/:jobId" element={<ProtectedRoute><GeneratingScreen /></ProtectedRoute>} />
        <Route path="/result/:artifactId" element={<ProtectedRoute><ResultScreen /></ProtectedRoute>} />
        <Route path="/regenerate/:artifactId" element={<ProtectedRoute><RegenerateScreen /></ProtectedRoute>} />
        <Route path="/share/:artifactId" element={<ProtectedRoute><ShareScreen /></ProtectedRoute>} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  )
}

export default App
