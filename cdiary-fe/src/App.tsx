import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { HomeScreen } from './pages/HomeScreen';
import { LoginScreen } from './pages/LoginScreen';
import { CharacterCreationScreen } from './pages/CharacterCreationScreen';
import { WriteDiaryScreen } from './pages/WriteDiaryScreen';
import { OptionsScreen } from './pages/OptionsScreen';
import { GeneratingScreen } from './pages/GeneratingScreen';
import { ResultScreen } from './pages/ResultScreen';
import { RegenerateScreen } from './pages/RegenerateScreen';
import { ShareScreen } from './pages/ShareScreen';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LoginScreen />} />
        <Route path="/home" element={<HomeScreen />} />
        <Route path="/character-create" element={<CharacterCreationScreen />} />
        <Route path="/write" element={<WriteDiaryScreen />} />
        <Route path="/options" element={<OptionsScreen />} />
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
