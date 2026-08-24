import { lazy, Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom'
import { ThemeProvider } from './contexts/ThemeContext'
import { Navbar } from './components/Layout/Navbar'
import { Footer } from './components/Layout/Footer'

// Lazy-load page components for code splitting
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Runs = lazy(() => import('./pages/Runs'))
const RunDetail = lazy(() => import('./pages/RunDetail'))
const Compare = lazy(() => import('./pages/Compare'))
const NewAudit = lazy(() => import('./pages/NewAudit'))
const Settings = lazy(() => import('./pages/Settings'))
const ClientIntake = lazy(() => import('./pages/ClientIntake'))

/* ─── Loading Fallback ─── */
function PageLoader() {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: 200,
    }}>
      <div style={{
        width: 24,
        height: 24,
        border: '2px solid rgba(255,255,255,0.1)',
        borderTopColor: 'var(--accent-primary)',
        borderRadius: '50%',
        animation: 'spin 0.8s linear infinite',
      }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

function AnimatedRoutes() {
  const location = useLocation()
  return (
    <div key={location.pathname} className="page-transition">
      <Suspense fallback={<PageLoader />}>
        <Routes location={location}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/runs" element={<Runs />} />
          <Route path="/runs/:runId" element={<RunDetail />} />
          <Route path="/compare" element={<Compare />} />
          <Route path="/new-audit" element={<NewAudit />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/clients" element={<ClientIntake />} />
        </Routes>
      </Suspense>
    </div>
  )
}

function App() {
  return (
    <ThemeProvider>
      <Router>
        <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
          <Navbar />
          <main style={{ flex: 1, padding: '24px 0' }}>
            <AnimatedRoutes />
          </main>
          <Footer />
        </div>
      </Router>
    </ThemeProvider>
  )
}

export default App
