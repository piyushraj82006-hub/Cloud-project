import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  ShieldCheck,
  Lightning,
  Clock,
  ChartBar,
  ArrowRight,
  MagnifyingGlass,
  Bell,
  GitDiff,
} from '@phosphor-icons/react'
import '../styles/landing.css'

/* ─── Animated counter hook ─── */
function useCountUp(target: number, duration: number = 1600, startOnView: boolean = true) {
  const [count, setCount] = useState(0)
  const ref = useRef<HTMLDivElement>(null)
  const hasAnimated = useRef(false)

  useEffect(() => {
    if (!startOnView || !ref.current) return
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasAnimated.current) {
          hasAnimated.current = true
          const start = performance.now()
          const animate = (now: number) => {
            const elapsed = now - start
            const progress = Math.min(elapsed / duration, 1)
            const eased = 1 - Math.pow(1 - progress, 3)
            setCount(Math.round(eased * target))
            if (progress < 1) requestAnimationFrame(animate)
          }
          requestAnimationFrame(animate)
        }
      },
      { threshold: 0.3 }
    )
    observer.observe(ref.current)
    return () => observer.disconnect()
  }, [target, duration, startOnView])

  return { count, ref }
}

/* ─── Fade-in on scroll hook ─── */
function useInView(threshold = 0.15) {
  const ref = useRef<HTMLDivElement>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (!ref.current) return
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true)
          observer.disconnect()
        }
      },
      { threshold }
    )
    observer.observe(ref.current)
    return () => observer.disconnect()
  }, [threshold])

  return { ref, visible }
}

/* ─── Metric card ─── */
function MetricCard({ value, suffix, label }: { value: number; suffix: string; label: string }) {
  const { count, ref } = useCountUp(value, 1800)
  return (
    <div ref={ref} className="metric-card">
      <div className="metric-value">
        {count}{suffix}
      </div>
      <div className="metric-label">{label}</div>
    </div>
  )
}

/* ─── Feature card ─── */
function FeatureCard({
  icon: Icon,
  title,
  description,
  delay,
}: {
  icon: typeof ShieldCheck
  title: string
  description: string
  delay: number
}) {
  const { ref, visible } = useInView()
  return (
    <div
      ref={ref}
      className={`feature-card ${visible ? 'feature-card--visible' : ''}`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      <div className="feature-icon">
        <Icon size={20} weight="regular" />
      </div>
      <h3 className="feature-title">{title}</h3>
      <p className="feature-desc">{description}</p>
    </div>
  )
}

/* ─── Step item ─── */
function StepItem({
  number,
  title,
  description,
  delay,
}: {
  number: string
  title: string
  description: string
  delay: number
}) {
  const { ref, visible } = useInView()
  return (
    <div
      ref={ref}
      className={`step-item ${visible ? 'step-item--visible' : ''}`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      <div className="step-number">{number}</div>
      <div className="step-content">
        <h3 className="step-title">{title}</h3>
        <p className="step-desc">{description}</p>
      </div>
    </div>
  )
}

/* ─── Landing Page ─── */
export default function LandingPage() {
  const [heroVisible, setHeroVisible] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setHeroVisible(true), 100)
    return () => clearTimeout(timer)
  }, [])

  return (
    <div className="landing">
      {/* ─── Hero ─── */}
      <section className="hero">
        <div className="hero-inner">
          <div className={`hero-content ${heroVisible ? 'hero-content--visible' : ''}`}>
            <div className="hero-badge">
              <ShieldCheck size={13} weight="regular" />
              Automated resilience testing
            </div>
            <h1 className="hero-title">
              Know your systems<br />
              recover before they fail
            </h1>
            <p className="hero-subtitle">
              CloudGuard DR runs controlled fault injection tests against your infrastructure,
              measures actual recovery time, and scores your resilience. No assumptions, no guesswork.
            </p>
            <div className="hero-actions">
              <Link to="/app" className="btn-hero-primary">
                Start testing
                <ArrowRight size={15} weight="bold" />
              </Link>
              <a href="#features" className="btn-hero-secondary">
                See how it works
              </a>
            </div>
          </div>

          <div className={`hero-visual ${heroVisible ? 'hero-visual--visible' : ''}`}>
            <div className="hero-preview">
              <div className="preview-header">
                <div className="preview-dots">
                  <span /><span /><span />
                </div>
                <span className="preview-title">CloudGuard DR Dashboard</span>
              </div>
              <div className="preview-body">
                <div className="preview-score-ring">
                  <svg viewBox="0 0 120 120" className="score-svg">
                    <circle cx="60" cy="60" r="52" fill="none" stroke="rgba(0,0,0,0.06)" strokeWidth="6" />
                    <circle
                      cx="60" cy="60" r="52"
                      fill="none"
                      stroke="#3e77e8"
                      strokeWidth="6"
                      strokeLinecap="round"
                      strokeDasharray="326.7"
                      strokeDashoffset="58.8"
                      className="score-ring"
                    />
                  </svg>
                  <div className="score-value">82</div>
                </div>
                <div className="preview-metrics">
                  <div className="preview-metric">
                    <span className="preview-metric-label">RTO</span>
                    <span className="preview-metric-value">2m 32s</span>
                  </div>
                  <div className="preview-metric">
                    <span className="preview-metric-label">RPO</span>
                    <span className="preview-metric-value">45s</span>
                  </div>
                  <div className="preview-metric">
                    <span className="preview-metric-label">Status</span>
                    <span className="preview-metric-value preview-metric-value--pass">Passed</span>
                  </div>
                </div>
                <div className="preview-timeline">
                  <div className="timeline-bar">
                    <div className="timeline-segment timeline-segment--inject" style={{ width: '15%' }} />
                    <div className="timeline-segment timeline-segment--monitor" style={{ width: '45%' }} />
                    <div className="timeline-segment timeline-segment--recover" style={{ width: '25%' }} />
                  </div>
                  <div className="timeline-labels">
                    <span>Inject</span>
                    <span>Monitor</span>
                    <span>Recover</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Metrics ─── */}
      <section className="metrics-section">
        <div className="container">
          <div className="metrics-grid">
            <MetricCard value={82} suffix="%" label="Average resilience score across deployments" />
            <MetricCard value={3} suffix="min" label="Mean recovery time under fault injection" />
            <MetricCard value={99} suffix=".7%" label="Successful recovery rate in production tests" />
          </div>
        </div>
      </section>

      {/* ─── Features ─── */}
      <section id="features" className="features-section">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">Built for teams that take reliability seriously</h2>
            <p className="section-subtitle">
              Stop guessing whether your disaster recovery plan works. Test it. Measure it. Improve it.
            </p>
          </div>
          <div className="features-grid">
            <FeatureCard
              icon={Lightning}
              title="Fault injection"
              description="Trigger real failure scenarios: EC2 termination, DNS disruption, S3 origin blocking. Test what actually happens when things break."
              delay={0}
            />
            <FeatureCard
              icon={Clock}
              title="Recovery measurement"
              description="Automated monitoring polls health checks every 15 seconds, measuring your exact RTO and RPO from the moment of failure."
              delay={80}
            />
            <FeatureCard
              icon={ChartBar}
              title="Resilience scoring"
              description="Convert raw recovery data into a 0-100 score weighted by business impact. Track trends over time across every deployment."
              delay={160}
            />
            <FeatureCard
              icon={MagnifyingGlass}
              title="SEO & health audits"
              description="Beyond DR testing: run external site audits checking HTTPS, DNS, response times, meta tags, and structured data."
              delay={240}
            />
            <FeatureCard
              icon={GitDiff}
              title="Competitive analysis"
              description="Compare your site's technical health against competitors. Find gaps in performance, SEO, and infrastructure resilience."
              delay={320}
            />
            <FeatureCard
              icon={Bell}
              title="Automated alerts"
              description="Get notified via SNS when recovery times exceed thresholds or scores drop below targets. Weekly cron or on-demand."
              delay={400}
            />
          </div>
        </div>
      </section>

      {/* ─── How it works ─── */}
      <section className="process-section">
        <div className="container">
          <div className="process-layout">
            <div className="process-header">
              <h2 className="section-title">From fault to insight in four steps</h2>
              <p className="section-subtitle">
                Every test follows the same controlled pipeline. Inject a fault, monitor recovery,
                measure the results, and get a scored report.
              </p>
            </div>
            <div className="steps-list">
              <StepItem
                number="01"
                title="Inject"
                description="AWS FIS terminates a tagged EC2 instance, blocks an S3 origin, or disrupts a security group."
                delay={0}
              />
              <StepItem
                number="02"
                title="Monitor"
                description="CloudWatch and ALB health checks are polled every 15 seconds until recovery or timeout."
                delay={100}
              />
              <StepItem
                number="03"
                title="Measure"
                description="RTO is calculated from injection to recovery. RPO from last known good state. Both are stored in DynamoDB."
                delay={200}
              />
              <StepItem
                number="04"
                title="Report"
                description="A 0-100 resilience score is generated, a PDF report is built, and alerts are sent to your team."
                delay={300}
              />
            </div>
          </div>
        </div>
      </section>

      {/* ─── CTA ─── */}
      <section className="cta-section">
        <div className="container">
          <div className="cta-card">
            <h2 className="cta-title">Start testing your resilience today</h2>
            <p className="cta-subtitle">
              Run your first fault injection test in under five minutes. No credit card required.
            </p>
            <div className="cta-actions">
              <Link to="/app" className="btn-cta-primary">
                Launch dashboard
                <ArrowRight size={15} weight="bold" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Footer ─── */}
      <footer className="landing-footer">
        <div className="container">
          <div className="footer-inner">
            <div className="footer-brand">
              <span className="footer-logo">CloudGuard DR</span>
              <span className="footer-tagline">Automated disaster recovery testing</span>
            </div>
            <div className="footer-links">
              <a href="#features">Features</a>
              <a href="#how-it-works">How it works</a>
              <Link to="/app">Dashboard</Link>
            </div>
            <div className="footer-legal">
              <span>&copy; 2026 CloudGuard DR</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
