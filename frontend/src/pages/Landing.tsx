import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import {
  Bot,
  BookOpen,
  Phone,
  BarChart3,
  ArrowRight,
  ChevronRight,
  Zap,
  Shield,
  Clock,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { AnimatedBackground } from "@/components/AnimatedBackground";

const features = [
  {
    icon: Bot,
    title: "Create AI Voice Agents",
    description: "Build intelligent agents with custom personalities and behaviors",
  },
  {
    icon: BookOpen,
    title: "Upload Knowledge Base",
    description: "Feed your agents with documents, PDFs, and custom data",
  },
  {
    icon: Phone,
    title: "Make & Receive Calls",
    description: "Assign phone numbers and start handling calls 24/7",
  },
  {
    icon: BarChart3,
    title: "Analyze Conversations",
    description: "Get insights, transcripts, and analytics on every call",
  },
];

const steps = [
  { number: "01", title: "Create Agent", description: "Design your AI voice agent" },
  { number: "02", title: "Add Knowledge", description: "Upload your data" },
  { number: "03", title: "Buy Phone Number", description: "Get a dedicated line" },
  { number: "04", title: "Start Calling", description: "Go live instantly" },
  { number: "05", title: "View Analytics", description: "Track performance" },
];

const benefits = [
  { icon: Zap, title: "Deploy in Minutes", description: "No code required" },
  { icon: Shield, title: "Enterprise Security", description: "SOC2 compliant" },
  { icon: Clock, title: "24/7 Availability", description: "Never miss a call" },
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="relative z-10 border-b border-border/50 backdrop-blur-sm">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link to="/" className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
              <Bot className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-lg font-semibold text-foreground">VoiceAI</span>
          </Link>

          <nav className="hidden items-center gap-8 md:flex">
            <Link to="#features" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Features
            </Link>
            <Link to="#how-it-works" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              How it Works
            </Link>
          </nav>

          <div className="flex items-center gap-3">
            <Button asChild variant="ghost" className="text-foreground">
              <Link to="/login">Sign in</Link>
            </Button>
            <Button asChild>
              <Link to="/signup">Get Started</Link>
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden py-20 lg:py-32">
        <AnimatedBackground />
        <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid items-center gap-12 lg:grid-cols-2">
            {/* Left - Text */}
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
            >
              <h1 className="mb-6 text-4xl font-bold tracking-tight text-foreground sm:text-5xl lg:text-6xl">
                Build, deploy & scale{" "}
                <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">AI voice agents</span> in minutes.
              </h1>
              <p className="mb-8 max-w-lg text-lg text-muted-foreground">
                Upload knowledge. Assign a phone number. Make calls. Track everything.
                The complete platform for AI-powered voice automation.
              </p>
              <div className="flex flex-col gap-4 sm:flex-row">
                <Button asChild size="lg" className="text-base">
                  <Link to="/signup">
                    Create your first agent
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Link>
                </Button>
                <Button asChild variant="outline" size="lg" className="text-base border-border text-foreground hover:bg-accent">
                  <Link to="/login">View demo calls</Link>
                </Button>
              </div>
            </motion.div>

            {/* Right - Flow Diagram */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="hidden lg:block"
            >
              <div className="glass-card relative p-8">
                <div className="flex items-center justify-center gap-6">
                  {[
                    { icon: BookOpen, label: "Knowledge" },
                    { icon: Bot, label: "Agent" },
                    { icon: Phone, label: "Phone" },
                    { icon: BarChart3, label: "Analytics" },
                  ].map((item, index) => (
                    <motion.div
                      key={item.label}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.4 + index * 0.1 }}
                      className="flex flex-col items-center"
                    >
                      <motion.div 
                        className="flex h-16 w-16 items-center justify-center rounded-xl bg-primary/20 border border-primary/30"
                        whileHover={{ scale: 1.1, borderColor: "hsl(var(--primary))" }}
                        transition={{ type: "spring", stiffness: 300 }}
                      >
                        <item.icon className="h-8 w-8 text-primary" />
                      </motion.div>
                      <span className="mt-3 text-sm font-medium text-foreground">
                        {item.label}
                      </span>
                      {index < 3 && (
                        <motion.div
                          className="absolute"
                          style={{ left: `${22 + index * 25}%`, top: '42%' }}
                          animate={{ x: [0, 5, 0] }}
                          transition={{ duration: 1.5, repeat: Infinity }}
                        >
                          <ChevronRight className="h-5 w-5 text-primary/60" />
                        </motion.div>
                      )}
                    </motion.div>
                  ))}
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="border-t border-border bg-muted/30 py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mb-12 text-center"
          >
            <h2 className="mb-4 text-3xl font-bold">What You Can Do</h2>
            <p className="text-lg text-muted-foreground">
              Everything you need to automate voice interactions
            </p>
          </motion.div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
              >
                <Card className="h-full transition-colors hover:bg-accent/50">
                  <CardContent className="p-6">
                    <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                      <feature.icon className="h-6 w-6 text-primary" />
                    </div>
                    <h3 className="mb-2 font-semibold">{feature.title}</h3>
                    <p className="text-sm text-muted-foreground">
                      {feature.description}
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How it Works Section */}
      <section id="how-it-works" className="py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mb-12 text-center"
          >
            <h2 className="mb-4 text-3xl font-bold">How It Works</h2>
            <p className="text-lg text-muted-foreground">
              From setup to production in 5 simple steps
            </p>
          </motion.div>

          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-1/2 top-0 hidden h-full w-px -translate-x-1/2 bg-border lg:block" />

            <div className="grid gap-8 lg:gap-0">
              {steps.map((step, index) => (
                <motion.div
                  key={step.number}
                  initial={{ opacity: 0, x: index % 2 === 0 ? -20 : 20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.1 }}
                  className={`flex items-center gap-6 lg:gap-12 ${
                    index % 2 === 0 ? "lg:flex-row" : "lg:flex-row-reverse"
                  }`}
                >
                  <div className={`flex-1 ${index % 2 === 0 ? "lg:text-right" : "lg:text-left"}`}>
                    <span className="text-4xl font-bold text-primary/20">{step.number}</span>
                    <h3 className="text-xl font-semibold">{step.title}</h3>
                    <p className="text-muted-foreground">{step.description}</p>
                  </div>
                  <div className="relative z-10 flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                    {index + 1}
                  </div>
                  <div className="hidden flex-1 lg:block" />
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="border-t border-border bg-muted/30 py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid gap-8 md:grid-cols-3">
            {benefits.map((benefit, index) => (
              <motion.div
                key={benefit.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="flex items-start gap-4"
              >
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                  <benefit.icon className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold">{benefit.title}</h3>
                  <p className="text-sm text-muted-foreground">{benefit.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="glass-card rounded-2xl p-8 text-center lg:p-16"
          >
            <h2 className="mb-4 text-3xl font-bold lg:text-4xl">
              Ready to automate your calls?
            </h2>
            <p className="mb-8 text-lg text-muted-foreground">
              Start building your AI voice agent today. No credit card required.
            </p>
            <Button asChild size="lg" className="text-base">
              <Link to="/signup">
                Get started for free
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            </Button>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
                <Bot className="h-4 w-4 text-primary-foreground" />
              </div>
              <span className="font-semibold">VoiceAI</span>
            </div>
            <nav className="flex gap-6 text-sm text-muted-foreground">
              <a href="#" className="hover:text-foreground">Docs</a>
              <a href="#" className="hover:text-foreground">Privacy</a>
              <a href="#" className="hover:text-foreground">Terms</a>
              <a href="#" className="hover:text-foreground">Contact</a>
            </nav>
          </div>
        </div>
      </footer>
    </div>
  );
}
