import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom'
import { Navbar } from './components/Layout/Navbar'
import { Footer } from './components/Layout/Footer'
import Dashboard from './pages/Dashboard'
import Runs from './pages/Runs'
import RunDetail from './pages/RunDetail'
import Compare from './pages/Compare'
import NewAudit from './pages/NewAudit'
import Settings from './pages/Settings'
import ClientIntake from './pages/ClientIntake'

function AnimatedRoutes() {
  const location = useLocation()
  return (
    <div key={location.pathname} className="page-transition">
      <Routes location={location}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/runs" element={<Runs />} />
        <Route path="/runs/:runId" element={<RunDetail />} />
        <Route path="/compare" element={<Compare />} />
        <Route path="/new-audit" element={<NewAudit />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/clients" element={<ClientIntake />} />
      </Routes>
    </div>
  )
}

function App() {
  return (
    <Router>
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <Navbar />
        <main style={{ flex: 1, padding: '24px 0' }}>
          <AnimatedRoutes />
        </main>
        <Footer />
      </div>
    </Router>
  )
}

export default App
