import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Terminal, Shield, Zap, Globe } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 selection:bg-blue-500/30">
      {/* Navigation */}
      <nav className="border-b border-slate-800 bg-slate-950/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center font-bold text-lg">H</div>
            <span className="font-semibold text-lg tracking-tight">Hushh Tunnel</span>
          </div>
          <div className="flex items-center space-x-4">
            <Link href="https://github.com/nikhil-v/hushh" target="_blank" className="text-slate-400 hover:text-white transition font-medium text-sm">
              GitHub
            </Link>
            <Link href="/login">
              <Button variant="ghost" className="text-slate-300 hover:text-white">Login</Button>
            </Link>
            <Link href="/register">
              <Button className="bg-blue-600 hover:bg-blue-700 text-white">Get Started</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main>
        <section className="py-24 sm:py-32 relative overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-900/20 via-slate-950 to-slate-950"></div>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
            <h1 className="text-5xl sm:text-7xl font-extrabold tracking-tight mb-8">
              Expose localhost <br className="hidden sm:block" />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">securely in seconds.</span>
            </h1>
            <p className="text-lg sm:text-xl text-slate-400 max-w-2xl mx-auto mb-10">
              Hushh Tunnel lets developers expose local applications over HTTPS using a single command. 
              No firewall changes. No DNS propagation.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/register">
                <Button size="lg" className="bg-blue-600 hover:bg-blue-700 text-white px-8 h-12 text-base">
                  Start Tunneling for Free
                </Button>
              </Link>
              <div className="flex items-center bg-slate-900 border border-slate-800 rounded-md px-4 h-12 font-mono text-sm text-slate-300">
                <span className="text-slate-500 mr-2">$</span> pip install hushh-tunnel
              </div>
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="py-24 bg-slate-900/50 border-y border-slate-800">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <Card className="bg-slate-900/50 border-slate-800">
                <CardContent className="pt-6">
                  <div className="w-12 h-12 bg-blue-500/10 rounded-lg flex items-center justify-center mb-4 text-blue-400">
                    <Zap className="w-6 h-6" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2">Instant Setup</h3>
                  <p className="text-slate-400">One pip install and you're ready. Expose any local port to the internet instantly.</p>
                </CardContent>
              </Card>
              <Card className="bg-slate-900/50 border-slate-800">
                <CardContent className="pt-6">
                  <div className="w-12 h-12 bg-emerald-500/10 rounded-lg flex items-center justify-center mb-4 text-emerald-400">
                    <Shield className="w-6 h-6" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2">Secure by Default</h3>
                  <p className="text-slate-400">End-to-end TLS encryption automatically provisioned. Protect your traffic from prying eyes.</p>
                </CardContent>
              </Card>
              <Card className="bg-slate-900/50 border-slate-800">
                <CardContent className="pt-6">
                  <div className="w-12 h-12 bg-purple-500/10 rounded-lg flex items-center justify-center mb-4 text-purple-400">
                    <Globe className="w-6 h-6" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2">Global Edge</h3>
                  <p className="text-slate-400">Low latency routing ensuring fast connections from anywhere in the world.</p>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* Installation */}
        <section className="py-24">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h2 className="text-3xl font-bold mb-12">Three steps to public</h2>
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-left max-w-2xl mx-auto font-mono text-sm overflow-x-auto shadow-2xl">
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
              </div>
              <div className="space-y-4 text-slate-300">
                <p><span className="text-slate-500"># 1. Install the CLI via pip</span><br/>
                <span className="text-blue-400">$</span> pip install hushh-tunnel</p>
                
                <p><span className="text-slate-500"># 2. Authenticate your machine</span><br/>
                <span className="text-blue-400">$</span> hushh login</p>
                
                <p><span className="text-slate-500"># 3. Expose your local port</span><br/>
                <span className="text-blue-400">$</span> hushh http 3000<br/>
                <span className="text-emerald-400">Forwarding: https://your-subdomain.hushh.online -&gt; localhost:3000</span></p>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-800 py-12 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between">
          <div className="flex items-center space-x-2 mb-4 md:mb-0">
            <div className="w-6 h-6 bg-slate-800 rounded flex items-center justify-center font-bold text-xs text-slate-400">H</div>
            <span className="text-slate-500 text-sm">© {new Date().getFullYear()} Hushh Tunnel.</span>
          </div>
          <div className="flex space-x-6 text-sm text-slate-500">
            <Link href="https://github.com/nikhil-v/hushh" className="hover:text-slate-300">GitHub</Link>
            <Link href="/docs" className="hover:text-slate-300">Documentation</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
