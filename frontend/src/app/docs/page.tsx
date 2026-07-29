import Link from 'next/link';
import { Card, CardContent } from '@/components/ui/card';

export default function DocumentationPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 selection:bg-blue-500/30">
      {/* Navigation */}
      <nav className="border-b border-slate-800 bg-slate-950/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center font-bold text-lg">H</div>
            <span className="font-semibold text-lg tracking-tight">Hushh Tunnel</span>
          </Link>
          <div className="flex items-center space-x-4">
            <Link href="/" className="text-slate-400 hover:text-white transition font-medium text-sm">
              Home
            </Link>
          </div>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <h1 className="text-4xl font-extrabold mb-8 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">Documentation</h1>
        
        <div className="space-y-12">
          {/* Quick Start */}
          <section>
            <h2 className="text-2xl font-bold mb-4 border-b border-slate-800 pb-2">Quick Start</h2>
            <Card className="bg-slate-900/50 border-slate-800 mb-6">
              <CardContent className="pt-6">
                <h3 className="text-xl font-semibold mb-2 text-white">1. Install the CLI</h3>
                <div className="bg-slate-950 p-4 rounded-md font-mono text-sm text-slate-300 mb-4 border border-slate-800">
                  <span className="text-slate-500">$</span> pip install hushh-tunnel
                </div>

                <h3 className="text-xl font-semibold mb-2 text-white">2. Login</h3>
                <div className="bg-slate-950 p-4 rounded-md font-mono text-sm text-slate-300 mb-4 border border-slate-800">
                  <span className="text-slate-500">$</span> hushh login
                  <br/>
                  <span className="text-slate-500"># Enter your email and password</span>
                </div>

                <h3 className="text-xl font-semibold mb-2 text-white">3. Expose a local service</h3>
                <div className="bg-slate-950 p-4 rounded-md font-mono text-sm text-slate-300 mb-4 border border-slate-800">
                  <span className="text-slate-500"># Start your local app first (e.g. on port 3000)</span>
                  <br/>
                  <span className="text-slate-500">$</span> hushh http 3000
                </div>

                <h3 className="text-xl font-semibold mb-2 text-white">4. Custom subdomain</h3>
                <div className="bg-slate-950 p-4 rounded-md font-mono text-sm text-slate-300 border border-slate-800">
                  <span className="text-slate-500">$</span> hushh http 8080 --subdomain myapi
                  <br/>
                  <span className="text-slate-500"># → https://myapi.hushh.online</span>
                </div>
              </CardContent>
            </Card>
          </section>

          {/* CLI Reference */}
          <section>
            <h2 className="text-2xl font-bold mb-4 border-b border-slate-800 pb-2">CLI Reference</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-300">
                    <th className="py-3 px-4 font-semibold">Command</th>
                    <th className="py-3 px-4 font-semibold">Description</th>
                  </tr>
                </thead>
                <tbody className="text-slate-400">
                  <tr className="border-b border-slate-800/50">
                    <td className="py-3 px-4 font-mono text-sm">hushh login</td>
                    <td className="py-3 px-4">Authenticate with the server</td>
                  </tr>
                  <tr className="border-b border-slate-800/50">
                    <td className="py-3 px-4 font-mono text-sm">hushh logout</td>
                    <td className="py-3 px-4">Clear local credentials</td>
                  </tr>
                  <tr className="border-b border-slate-800/50">
                    <td className="py-3 px-4 font-mono text-sm">hushh whoami</td>
                    <td className="py-3 px-4">Show current user</td>
                  </tr>
                  <tr className="border-b border-slate-800/50">
                    <td className="py-3 px-4 font-mono text-sm">hushh http &lt;port&gt;</td>
                    <td className="py-3 px-4">Open an HTTP tunnel</td>
                  </tr>
                  <tr className="border-b border-slate-800/50">
                    <td className="py-3 px-4 font-mono text-sm">hushh http &lt;port&gt; --subdomain &lt;name&gt;</td>
                    <td className="py-3 px-4">Open with custom subdomain</td>
                  </tr>
                  <tr className="border-b border-slate-800/50">
                    <td className="py-3 px-4 font-mono text-sm">hushh status</td>
                    <td className="py-3 px-4">List your active tunnels</td>
                  </tr>
                  <tr className="border-b border-slate-800/50">
                    <td className="py-3 px-4 font-mono text-sm">hushh stop &lt;subdomain&gt;</td>
                    <td className="py-3 px-4">Disconnect a tunnel</td>
                  </tr>
                  <tr>
                    <td className="py-3 px-4 font-mono text-sm">hushh version</td>
                    <td className="py-3 px-4">Show version</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </main>
      
      <footer className="border-t border-slate-800 py-12 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between">
          <div className="flex items-center space-x-2 mb-4 md:mb-0">
            <div className="w-6 h-6 bg-slate-800 rounded flex items-center justify-center font-bold text-xs text-slate-400">H</div>
            <span className="text-slate-500 text-sm">© {new Date().getFullYear()} Hushh Tunnel.</span>
          </div>
          <div className="flex space-x-6 text-sm text-slate-500">
            <Link href="https://github.com/nikhil-v/hushh" className="hover:text-slate-300">GitHub</Link>
            <Link href="/" className="hover:text-slate-300">Home</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
