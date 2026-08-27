import { lazy, Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom'
import { ThemeProvider } from './contexts/ThemeContext'
import { Navbar } from './components/Layout/Navbar'
import { Footer } from './components/Layout/Footer'

// Lazy-load page components for code splitting
const LandingPage = lazy(() => import('./pages/LandingPage'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Runs = lazy(() => import('./pages/Runs'))
const RunDetail = lazy(() => import('./pages/RunDetail'))
const Compare = lazy(() => import('./pages/Compare'))
const NewAudit = lazy(() => import('./pages/NewAudit'))
const Settings = lazy(() => import('./pages/Settings'))
const ClientIntake = lazy(() => import('./pages/ClientIntake'))
const NotFound = lazy(() => import('./pages/NotFound'))

/* ─── Loading Fallback ─── */
function PageLoader() {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: 200,
    }}>
      <div className="spinner" />
    </div>
  )
}

function AppShell() {
  const location = useLocation()
  const isLanding = location.pathname === '/'

  return (
    <>
      <a href="#main-content" className="skip-to-content">
        Skip to content
      </a>
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        {!isLanding && <Navbar />}
        <main id="main-content" style={{ flex: 1, padding: isLanding ? 0 : '24px 0' }} tabIndex={-1}>
          <div className="page-transition">
            <Suspense fallback={<PageLoader />}>
              <Routes location={location}>
                <Route path="/" element={<LandingPage />} />
                <Route path="/app" element={<Dashboard />} />
                <Route path="/runs" element={<Runs />} />
                <Route path="/runs/:runId" element={<RunDetail />} />
                <Route path="/compare" element={<Compare />} />
                <Route path="/new-audit" element={<NewAudit />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/clients" element={<ClientIntake />} />
                <Route path="*" element={<NotFound />} />
              </Routes>
            </Suspense>
          </div>
        </main>
        {!isLanding && <Footer />}
      </div>
    </>
  )
}

function App() {
  return (
    <ThemeProvider>
      <Router>
        <AppShell />
      </Router>
    </ThemeProvider>
  )
}

export default App
