import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { ArrowRight, Zap, GitBranch, Brain, Code } from 'lucide-react'

export default function Page() {
  return (
    <main className="min-h-screen relative overflow-hidden">
      {/* Animated background gradient */}
      <div className="absolute inset-0 gradient-bg opacity-10 animate-pulse-slow" />
      
      {/* Grid pattern overlay */}
      <div className="absolute inset-0" style={{
        backgroundImage: 'radial-gradient(circle at 1px 1px, hsl(var(--foreground) / 0.05) 1px, transparent 0)',
        backgroundSize: '40px 40px'
      }} />

      <div className="relative z-10 container mx-auto px-6 py-20">
        {/* Hero Section */}
        <div className="flex flex-col items-center justify-center min-h-[80vh] text-center space-y-8 animate-fade-in">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 backdrop-blur-sm animate-slide-up">
            <Zap className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium text-primary">Autonomous Coding Agent</span>
          </div>

          {/* Title */}
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight max-w-4xl animate-slide-up" style={{ animationDelay: '0.1s' }}>
            Welcome to{' '}
            <span className="gradient-text">AutoCodit Agent</span>
          </h1>

          {/* Description */}
          <p className="text-xl md:text-2xl text-muted-foreground max-w-2xl animate-slide-up" style={{ animationDelay: '0.2s' }}>
            Your intelligent AI-powered mission control dashboard for autonomous code generation, testing, and deployment
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 animate-slide-up" style={{ animationDelay: '0.3s' }}>
            <Link href="/dashboard">
              <Button size="lg" className="group px-8 py-6 text-lg shadow-lg hover:shadow-xl transition-all">
                Open Dashboard
                <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
            <Button size="lg" variant="outline" className="px-8 py-6 text-lg backdrop-blur-sm">
              Learn More
            </Button>
          </div>

          {/* Feature Cards */}
          <div className="grid md:grid-cols-3 gap-6 mt-20 w-full max-w-5xl animate-fade-in" style={{ animationDelay: '0.4s' }}>
            <FeatureCard 
              icon={<Brain className="w-8 h-8" />}
              title="AI-Powered"
              description="Advanced LLM integration for intelligent code generation and problem solving"
            />
            <FeatureCard 
              icon={<GitBranch className="w-8 h-8" />}
              title="Git Integration"
              description="Seamless GitHub integration with automated PR creation and code reviews"
            />
            <FeatureCard 
              icon={<Code className="w-8 h-8" />}
              title="Multi-Language"
              description="Support for multiple programming languages and frameworks"
            />
          </div>
        </div>

        {/* Stats Section */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 py-16 border-t border-border/50 animate-fade-in" style={{ animationDelay: '0.5s' }}>
          <StatCard number="100+" label="Tasks Completed" />
          <StatCard number="99.9%" label="Uptime" />
          <StatCard number="<100ms" label="Response Time" />
          <StatCard number="24/7" label="Availability" />
        </div>
      </div>
    </main>
  )
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="group relative rounded-2xl border bg-card p-6 shadow-sm hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
      <div className="relative space-y-3">
        <div className="inline-flex p-3 rounded-xl bg-primary/10 text-primary group-hover:scale-110 transition-transform">
          {icon}
        </div>
        <h3 className="text-xl font-semibold">{title}</h3>
        <p className="text-muted-foreground leading-relaxed">{description}</p>
      </div>
    </div>
  )
}

function StatCard({ number, label }: { number: string; label: string }) {
  return (
    <div className="text-center space-y-2">
      <div className="text-3xl md:text-4xl font-bold gradient-text">{number}</div>
      <div className="text-sm text-muted-foreground">{label}</div>
    </div>
  )
}
