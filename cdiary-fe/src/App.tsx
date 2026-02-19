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

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={localStorage.getItem('token') ? <Navigate to="/home" replace /> : <LoginScreen />} />
        <Route path="/signup" element={<SignUpScreen />} />
        <Route path="/signin" element={<SignInScreen />} />
        <Route path="/home" element={<HomeScreen />} />
        <Route path="/profile" element={<UserProfileScreen />} />
        <Route path="/character-create" element={<CharacterCreationScreen />} />
        <Route path="/write" element={<WriteDiaryScreen />} />
        <Route path="/generate/:jobId" element={<GeneratingScreen />} />
        <Route path="/result/:artifactId" element={<ResultScreen />} />
        <Route path="/regenerate/:artifactId" element={<RegenerateScreen />} />
        <Route path="/share/:artifactId" element={<ShareScreen />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  )
}

export default App
