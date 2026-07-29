import Link from 'next/link';
import { Card, CardContent } from '@/components/ui/card';
import { 
  Book, Zap, Shield, Globe, Terminal, Server, Code, 
  ChevronRight, Lock, Activity, Cpu
} from 'lucide-react';

export default function DocumentationPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 selection:bg-blue-500/30 font-sans">
      {/* Navigation */}
      <nav className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center font-bold text-lg shadow-lg shadow-blue-500/20">H</div>
            <span className="font-semibold text-lg tracking-tight">Hushh Tunnel</span>
          </Link>
          <div className="flex items-center space-x-6 text-sm font-medium">
            <Link href="/" className="text-slate-400 hover:text-white transition">Home</Link>
            <Link href="https://github.com/nikhil-v/hushh" target="_blank" className="text-slate-400 hover:text-white transition">GitHub</Link>
          </div>
        </div>
      </nav>

      <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row">
        
        {/* Sidebar */}
        <aside className="w-full md:w-64 shrink-0 py-8 md:pr-8 md:sticky md:top-16 md:h-[calc(100vh-4rem)] md:overflow-y-auto hidden md:block border-r border-slate-800/50 scrollbar-hide">
          <div className="space-y-8">
            <div>
              <h4 className="font-semibold text-slate-100 mb-3 px-2 text-sm uppercase tracking-wider">Getting Started</h4>
              <ul className="space-y-1">
                <li><a href="#overview" className="flex items-center text-sm text-slate-400 hover:text-white hover:bg-slate-900 px-2 py-1.5 rounded-md transition"><Book className="w-4 h-4 mr-2" /> Overview</a></li>
                <li><a href="#quickstart" className="flex items-center text-sm text-slate-400 hover:text-white hover:bg-slate-900 px-2 py-1.5 rounded-md transition"><Zap className="w-4 h-4 mr-2" /> Quick Start</a></li>
                <li><a href="#features" className="flex items-center text-sm text-slate-400 hover:text-white hover:bg-slate-900 px-2 py-1.5 rounded-md transition"><Shield className="w-4 h-4 mr-2" /> Features</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold text-slate-100 mb-3 px-2 text-sm uppercase tracking-wider">Guides & Examples</h4>
              <ul className="space-y-1">
                <li><a href="#examples" className="flex items-center text-sm text-slate-400 hover:text-white hover:bg-slate-900 px-2 py-1.5 rounded-md transition"><Code className="w-4 h-4 mr-2" /> Use Case Examples</a></li>
                <li><a href="#custom-subdomains" className="flex items-center text-sm text-slate-400 hover:text-white hover:bg-slate-900 px-2 py-1.5 rounded-md transition"><Globe className="w-4 h-4 mr-2" /> Custom Subdomains</a></li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-slate-100 mb-3 px-2 text-sm uppercase tracking-wider">Reference</h4>
              <ul className="space-y-1">
                <li><a href="#cli-reference" className="flex items-center text-sm text-slate-400 hover:text-white hover:bg-slate-900 px-2 py-1.5 rounded-md transition"><Terminal className="w-4 h-4 mr-2" /> CLI Reference</a></li>
                <li><a href="#api-reference" className="flex items-center text-sm text-slate-400 hover:text-white hover:bg-slate-900 px-2 py-1.5 rounded-md transition"><Server className="w-4 h-4 mr-2" /> REST API</a></li>
                <li><a href="#architecture" className="flex items-center text-sm text-slate-400 hover:text-white hover:bg-slate-900 px-2 py-1.5 rounded-md transition"><Cpu className="w-4 h-4 mr-2" /> Architecture</a></li>
              </ul>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 py-10 md:pl-10 md:max-w-4xl prose prose-invert prose-slate prose-pre:bg-slate-900 prose-pre:border prose-pre:border-slate-800">
          
          <div className="mb-12">
            <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-4 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
              Documentation
            </h1>
            <p className="text-xl text-slate-400">
              Everything you need to set up, configure, and scale your local environments to the internet with Hushh Tunnel.
            </p>
          </div>

          <section id="overview" className="scroll-mt-24 mb-16">
            <h2 className="text-3xl font-bold mb-6 border-b border-slate-800 pb-2">Overview</h2>
            <p className="text-slate-300 leading-relaxed mb-4">
              Hushh Tunnel is a production-ready, open-source reverse tunneling platform. It allows developers to expose local applications running on localhost to the public internet securely over HTTPS in seconds.
            </p>
            <p className="text-slate-300 leading-relaxed">
              Whether you're testing webhooks, presenting a demo to a client, or building a distributed architecture, Hushh Tunnel provides persistent, low-latency connections without the need for firewall changes or DNS propagation.
            </p>
          </section>

          <section id="quickstart" className="scroll-mt-24 mb-16">
            <h2 className="text-3xl font-bold mb-6 border-b border-slate-800 pb-2">Quick Start</h2>
            
            <div className="space-y-6">
              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
                <h3 className="text-xl font-semibold mb-3 flex items-center"><span className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-600/20 text-blue-400 text-sm mr-3">1</span> Install the CLI</h3>
                <p className="text-slate-400 mb-4 text-sm">Hushh Tunnel is distributed via PyPI. Install it globally using pip.</p>
                <div className="bg-slate-950 p-4 rounded-lg font-mono text-sm text-slate-300 border border-slate-800/50 shadow-inner">
                  <span className="text-slate-500 select-none">$ </span>pip install hushh-tunnel
                </div>
              </div>

              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
                <h3 className="text-xl font-semibold mb-3 flex items-center"><span className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-600/20 text-blue-400 text-sm mr-3">2</span> Authenticate</h3>
                <p className="text-slate-400 mb-4 text-sm">Log in to link your CLI with your account. You'll be prompted for your email and password.</p>
                <div className="bg-slate-950 p-4 rounded-lg font-mono text-sm text-slate-300 border border-slate-800/50 shadow-inner">
                  <span className="text-slate-500 select-none">$ </span>hushh login
                </div>
              </div>

              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
                <h3 className="text-xl font-semibold mb-3 flex items-center"><span className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-600/20 text-blue-400 text-sm mr-3">3</span> Expose a Local Service</h3>
                <p className="text-slate-400 mb-4 text-sm">Simply pass the port number where your local application is running.</p>
                <div className="bg-slate-950 p-4 rounded-lg font-mono text-sm text-slate-300 border border-slate-800/50 shadow-inner">
                  <span className="text-slate-500 select-none">$ </span>hushh http 3000
                  <br /><br />
                  <span className="text-emerald-400">✔ Connected</span><br />
                  <span className="text-slate-400">Forwarding:</span><br />
                  <span className="text-blue-400">https://a8x91kp3.hushh.online</span> <span className="text-slate-500">→</span> http://localhost:3000
                </div>
              </div>
            </div>
          </section>

          <section id="features" className="scroll-mt-24 mb-16">
            <h2 className="text-3xl font-bold mb-6 border-b border-slate-800 pb-2">Features</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Card className="bg-slate-900/40 border-slate-800/80">
                <CardContent className="pt-6">
                  <Lock className="w-6 h-6 text-emerald-400 mb-3" />
                  <h4 className="font-semibold text-white mb-2">Secure HTTPS by Default</h4>
                  <p className="text-sm text-slate-400">Automated wildcard TLS certificates via Caddy and Let's Encrypt protect all traffic end-to-end.</p>
                </CardContent>
              </Card>
              <Card className="bg-slate-900/40 border-slate-800/80">
                <CardContent className="pt-6">
                  <Activity className="w-6 h-6 text-blue-400 mb-3" />
                  <h4 className="font-semibold text-white mb-2">Persistent WebSockets</h4>
                  <p className="text-sm text-slate-400">Built on top of WebSockets for ultra-low latency and highly reliable connection streams.</p>
                </CardContent>
              </Card>
              <Card className="bg-slate-900/40 border-slate-800/80">
                <CardContent className="pt-6">
                  <Shield className="w-6 h-6 text-purple-400 mb-3" />
                  <h4 className="font-semibold text-white mb-2">API Key Auth</h4>
                  <p className="text-sm text-slate-400">Secure authentication with hashed API keys ensures only authorized devices can open tunnels.</p>
                </CardContent>
              </Card>
              <Card className="bg-slate-900/40 border-slate-800/80">
                <CardContent className="pt-6">
                  <Globe className="w-6 h-6 text-orange-400 mb-3" />
                  <h4 className="font-semibold text-white mb-2">Custom Subdomains</h4>
                  <p className="text-sm text-slate-400">Claim your own persistent subdomains for permanent URLs (e.g., api.hushh.online).</p>
                </CardContent>
              </Card>
            </div>
          </section>

          <section id="examples" className="scroll-mt-24 mb-16">
            <h2 className="text-3xl font-bold mb-6 border-b border-slate-800 pb-2">Examples</h2>
            
            <div className="mb-8">
              <h3 className="text-xl font-semibold mb-3 text-white">Exposing a Next.js / React App</h3>
              <p className="text-slate-400 mb-3">If you are running a standard React or Next.js app on port 3000, simply run:</p>
              <div className="bg-slate-950 p-4 rounded-lg font-mono text-sm text-slate-300 border border-slate-800">
                <span className="text-slate-500">$ </span>npm run dev <span className="text-slate-500"># starts app on port 3000</span><br />
                <span className="text-slate-500">$ </span>hushh http 3000
              </div>
            </div>

            <div className="mb-8">
              <h3 className="text-xl font-semibold mb-3 text-white">Testing Webhooks with FastAPI/Flask</h3>
              <p className="text-slate-400 mb-3">When testing Stripe, GitHub, or Twilio webhooks locally (usually on port 8000), you can expose your local server directly:</p>
              <div className="bg-slate-950 p-4 rounded-lg font-mono text-sm text-slate-300 border border-slate-800">
                <span className="text-slate-500">$ </span>uvicorn main:app --port 8000<br />
                <span className="text-slate-500">$ </span>hushh http 8000
              </div>
              <p className="text-slate-400 mt-3 text-sm italic">You can now paste the generated `https://[id].hushh.online/webhook` URL directly into the external service provider.</p>
            </div>
          </section>

          <section id="custom-subdomains" className="scroll-mt-24 mb-16">
            <h2 className="text-3xl font-bold mb-6 border-b border-slate-800 pb-2">Custom Subdomains</h2>
            <p className="text-slate-300 mb-4">
              By default, Hushh generates a random alphanumeric string for your tunnel (e.g., `a8x91kp3.hushh.online`). 
              For predictable URLs across restarts, you can specify a custom subdomain.
            </p>
            <div className="bg-slate-950 p-4 rounded-lg font-mono text-sm text-slate-300 border border-slate-800 mb-4">
              <span className="text-slate-500">$ </span>hushh http 8080 --subdomain my-awesome-api
              <br /><br />
              <span className="text-emerald-400">✔ Connected</span><br />
              <span className="text-blue-400">https://my-awesome-api.hushh.online</span> <span className="text-slate-500">→</span> http://localhost:8080
            </div>
            <div className="bg-blue-900/20 border border-blue-900/50 rounded-lg p-4 flex items-start">
              <Book className="w-5 h-5 text-blue-400 mr-3 shrink-0 mt-0.5" />
              <p className="text-sm text-blue-200 m-0">
                <strong>Note:</strong> Custom subdomains are available on a first-come, first-served basis for the duration of the connection unless reserved via a Pro account.
              </p>
            </div>
          </section>

          <section id="cli-reference" className="scroll-mt-24 mb-16">
            <h2 className="text-3xl font-bold mb-6 border-b border-slate-800 pb-2">CLI Reference</h2>
            <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/50">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-900 border-b border-slate-800">
                    <th className="py-3 px-4 font-semibold text-slate-200">Command</th>
                    <th className="py-3 px-4 font-semibold text-slate-200">Description</th>
                  </tr>
                </thead>
                <tbody className="text-slate-400 divide-y divide-slate-800/50">
                  <tr className="hover:bg-slate-800/30 transition">
                    <td className="py-3 px-4 font-mono text-sm text-blue-300">hushh login</td>
                    <td className="py-3 px-4 text-sm">Authenticate your CLI with the server.</td>
                  </tr>
                  <tr className="hover:bg-slate-800/30 transition">
                    <td className="py-3 px-4 font-mono text-sm text-blue-300">hushh logout</td>
                    <td className="py-3 px-4 text-sm">Clear local credentials and API keys.</td>
                  </tr>
                  <tr className="hover:bg-slate-800/30 transition">
                    <td className="py-3 px-4 font-mono text-sm text-blue-300">hushh whoami</td>
                    <td className="py-3 px-4 text-sm">Show the currently authenticated user.</td>
                  </tr>
                  <tr className="hover:bg-slate-800/30 transition">
                    <td className="py-3 px-4 font-mono text-sm text-blue-300">hushh http &lt;port&gt;</td>
                    <td className="py-3 px-4 text-sm">Open an HTTP tunnel to the specified local port.</td>
                  </tr>
                  <tr className="hover:bg-slate-800/30 transition">
                    <td className="py-3 px-4 font-mono text-sm text-blue-300">hushh http &lt;port&gt; --subdomain &lt;name&gt;</td>
                    <td className="py-3 px-4 text-sm">Open an HTTP tunnel using a custom subdomain.</td>
                  </tr>
                  <tr className="hover:bg-slate-800/30 transition">
                    <td className="py-3 px-4 font-mono text-sm text-blue-300">hushh status</td>
                    <td className="py-3 px-4 text-sm">List all your currently active tunnels.</td>
                  </tr>
                  <tr className="hover:bg-slate-800/30 transition">
                    <td className="py-3 px-4 font-mono text-sm text-blue-300">hushh stop &lt;subdomain&gt;</td>
                    <td className="py-3 px-4 text-sm">Disconnect a specific active tunnel.</td>
                  </tr>
                  <tr className="hover:bg-slate-800/30 transition">
                    <td className="py-3 px-4 font-mono text-sm text-blue-300">hushh version</td>
                    <td className="py-3 px-4 text-sm">Show the installed CLI version.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <section id="api-reference" className="scroll-mt-24 mb-16">
            <h2 className="text-3xl font-bold mb-6 border-b border-slate-800 pb-2">REST API Reference</h2>
            <p className="text-slate-300 mb-4">
              Hushh Tunnel exposes a REST API for managing users, querying active tunnels, and monitoring server health programmatically.
            </p>
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
              <div className="border-b border-slate-800 p-4">
                <div className="flex items-center gap-3 mb-1">
                  <span className="text-xs font-bold px-2 py-1 bg-green-500/20 text-green-400 rounded">GET</span>
                  <code className="font-mono text-sm text-slate-200">/api/tunnels</code>
                </div>
                <p className="text-sm text-slate-400 mt-2">Returns a JSON array of your active tunnels.</p>
              </div>
              <div className="border-b border-slate-800 p-4">
                <div className="flex items-center gap-3 mb-1">
                  <span className="text-xs font-bold px-2 py-1 bg-red-500/20 text-red-400 rounded">DELETE</span>
                  <code className="font-mono text-sm text-slate-200">/api/tunnels/&#123;subdomain&#125;</code>
                </div>
                <p className="text-sm text-slate-400 mt-2">Force-stops an active tunnel by its subdomain.</p>
              </div>
              <div className="border-b border-slate-800 p-4">
                <div className="flex items-center gap-3 mb-1">
                  <span className="text-xs font-bold px-2 py-1 bg-blue-500/20 text-blue-400 rounded">POST</span>
                  <code className="font-mono text-sm text-slate-200">/auth/login</code>
                </div>
                <p className="text-sm text-slate-400 mt-2">Exchange email and password for a Bearer token and API Key.</p>
              </div>
              <div className="p-4">
                <div className="flex items-center gap-3 mb-1">
                  <span className="text-xs font-bold px-2 py-1 bg-green-500/20 text-green-400 rounded">GET</span>
                  <code className="font-mono text-sm text-slate-200">/metrics</code>
                </div>
                <p className="text-sm text-slate-400 mt-2">Returns Prometheus-formatted metrics of server performance.</p>
              </div>
            </div>
          </section>

          <section id="architecture" className="scroll-mt-24 mb-16">
            <h2 className="text-3xl font-bold mb-6 border-b border-slate-800 pb-2">Architecture</h2>
            <p className="text-slate-300 mb-4">
              Hushh Tunnel is built for speed and reliability, combining the best of reverse proxies and modern async python.
            </p>
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 font-mono text-xs sm:text-sm text-slate-400 overflow-x-auto">
              <pre className="!bg-transparent !p-0 !m-0 !border-0 text-slate-300">
{`Browser / External Client
      │
      ▼ HTTPS
[ Caddy Proxy ] (TLS termination, wildcard certs)
      │
      ▼ HTTP
[ FastAPI Server ] (hushh.online)
      │
      ├── REST API     (/auth, /api/tunnels, /metrics)
      │
      └── TunnelRoutingMiddleware
            │  (routes by Host header: <subdomain>.hushh.online)
            ▼
          [ TunnelManager ] (in-memory websocket registry)
            │
            ▼ Persistent WebSocket Connection
[ CLI Client ] (hushh http 3000)
            │
            ▼ HTTP
[ Localhost:3000 ]`}
              </pre>
            </div>
          </section>

        </main>
      </div>
      
    </div>
  );
}
