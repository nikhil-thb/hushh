"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Card, CardContent } from '@/components/ui/card';
import { 
  Book, Zap, Shield, Globe, Terminal, Code, Lock, Activity
} from 'lucide-react';

export default function DocumentationPage() {
  const [activeSection, setActiveSection] = useState('overview');

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        // Find the visible section with the largest intersection ratio
        let maxRatio = 0;
        let mostVisible = '';
        entries.forEach((entry) => {
          if (entry.isIntersecting && entry.intersectionRatio > maxRatio) {
            maxRatio = entry.intersectionRatio;
            mostVisible = entry.target.id;
          }
        });
        if (mostVisible) {
          setActiveSection(mostVisible);
        }
      },
      {
        rootMargin: '-20% 0px -60% 0px',
        threshold: [0, 0.1, 0.2, 0.5, 0.8, 1],
      }
    );

    const sections = document.querySelectorAll('section[id]');
    sections.forEach((section) => observer.observe(section));

    return () => {
      sections.forEach((section) => observer.unobserve(section));
    };
  }, []);

  const navItemClass = (id: string) => `flex items-center text-sm px-3 py-2 rounded-md transition ${
    activeSection === id 
      ? 'text-blue-600 dark:text-blue-400 bg-accent/80 font-medium shadow-sm' 
      : 'text-muted-foreground hover:text-foreground hover:bg-card'
  }`;

  return (
    <div className="min-h-screen bg-background text-foreground selection:bg-blue-500/30 font-sans">
      {/* Navigation */}
      <nav className="border-b border-border bg-background/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center font-bold text-lg text-primary-foreground shadow-lg shadow-blue-500/20">H</div>
            <span className="font-semibold text-lg tracking-tight">Hushh Tunnel</span>
          </Link>
          <div className="flex items-center space-x-6 text-sm font-medium">
            <Link href="/" className="text-muted-foreground hover:text-foreground transition">Home</Link>
            <Link href="https://github.com/nikhil-v/hushh" target="_blank" className="text-muted-foreground hover:text-foreground transition">GitHub</Link>
          </div>
        </div>
      </nav>

      <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row relative">
        
        {/* Sidebar */}
        <aside className="w-full md:w-64 shrink-0 py-8 md:pr-8 md:sticky md:top-16 md:h-[calc(100vh-4rem)] md:overflow-y-auto hidden md:block border-r border-border/50 scrollbar-hide">
          <div className="space-y-8">
            <div>
              <h4 className="font-semibold text-foreground mb-3 px-3 text-sm uppercase tracking-wider">Getting Started</h4>
              <ul className="space-y-1.5">
                <li><a href="#overview" className={navItemClass('overview')}><Book className="w-4 h-4 mr-2" /> Overview</a></li>
                <li><a href="#quickstart" className={navItemClass('quickstart')}><Zap className="w-4 h-4 mr-2" /> Quick Start</a></li>
                <li><a href="#features" className={navItemClass('features')}><Shield className="w-4 h-4 mr-2" /> Features</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold text-foreground mb-3 px-3 text-sm uppercase tracking-wider">Guides & Examples</h4>
              <ul className="space-y-1.5">
                <li><a href="#examples" className={navItemClass('examples')}><Code className="w-4 h-4 mr-2" /> Use Case Examples</a></li>
                <li><a href="#custom-subdomains" className={navItemClass('custom-subdomains')}><Globe className="w-4 h-4 mr-2" /> Custom Subdomains</a></li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-foreground mb-3 px-3 text-sm uppercase tracking-wider">Reference</h4>
              <ul className="space-y-1.5">
                <li><a href="#cli-reference" className={navItemClass('cli-reference')}><Terminal className="w-4 h-4 mr-2" /> CLI Reference</a></li>
              </ul>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 py-10 md:pl-10 md:max-w-4xl prose prose-invert prose-slate prose-pre:bg-card prose-pre:border prose-pre:border-border">
          
          <div className="mb-12">
            <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-4 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
              Documentation
            </h1>
            <p className="text-xl text-muted-foreground">
              Everything you need to expose your local environments to the internet with Hushh Tunnel.
            </p>
          </div>

          <section id="overview" className="scroll-mt-32 mb-20">
            <h2 className="text-3xl font-bold mb-6 border-b border-border pb-2">Overview</h2>
            <p className="text-muted-foreground leading-relaxed mb-4">
              Hushh Tunnel is a powerful reverse tunneling platform that allows you to expose local applications running on your machine to the public internet securely over HTTPS in seconds.
            </p>
            <p className="text-muted-foreground leading-relaxed">
              Whether you are testing webhooks, presenting a demo to a client, or accessing your local development server from a mobile device, Hushh Tunnel provides instant, reliable access without the need to modify your router's firewall or wait for DNS propagation.
            </p>
          </section>

          <section id="quickstart" className="scroll-mt-32 mb-20">
            <h2 className="text-3xl font-bold mb-6 border-b border-border pb-2">Quick Start</h2>
            
            <div className="space-y-6">
              <div className="bg-card border border-border rounded-xl p-6">
                <h3 className="text-xl font-semibold mb-3 flex items-center"><span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary/20 text-blue-600 dark:text-blue-400 text-sm mr-3">1</span> Install the Application</h3>
                <p className="text-muted-foreground mb-4 text-sm">Hushh Tunnel is distributed via Python's package manager. Install it easily using pip.</p>
                <div className="bg-background p-4 rounded-lg font-mono text-sm text-muted-foreground border border-border/50 shadow-inner">
                  <span className="text-muted-foreground select-none">$ </span>pip install hushh-tunnel
                </div>
              </div>

              <div className="bg-card border border-border rounded-xl p-6">
                <h3 className="text-xl font-semibold mb-3 flex items-center"><span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary/20 text-blue-600 dark:text-blue-400 text-sm mr-3">2</span> Log in to your Account</h3>
                <p className="text-muted-foreground mb-4 text-sm">Authenticate your device to securely link it with your account.</p>
                <div className="bg-background p-4 rounded-lg font-mono text-sm text-muted-foreground border border-border/50 shadow-inner">
                  <span className="text-muted-foreground select-none">$ </span>hushh login
                </div>
              </div>

              <div className="bg-card border border-border rounded-xl p-6">
                <h3 className="text-xl font-semibold mb-3 flex items-center"><span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary/20 text-blue-600 dark:text-blue-400 text-sm mr-3">3</span> Expose your Local Service</h3>
                <p className="text-muted-foreground mb-4 text-sm">Pass the port number where your local application is running to instantly create a public URL.</p>
                <div className="bg-background p-4 rounded-lg font-mono text-sm text-muted-foreground border border-border/50 shadow-inner">
                  <span className="text-muted-foreground select-none">$ </span>hushh http 3000
                  <br /><br />
                  <span className="text-emerald-400">✔ Connected</span><br />
                  <span className="text-muted-foreground">Forwarding:</span><br />
                  <span className="text-blue-600 dark:text-blue-400">https://a8x91kp3.hushh.online</span> <span className="text-muted-foreground">→</span> http://localhost:3000
                </div>
              </div>
            </div>
          </section>

          <section id="features" className="scroll-mt-32 mb-20">
            <h2 className="text-3xl font-bold mb-6 border-b border-border pb-2">Features</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Card className="bg-card/40 border-border/80">
                <CardContent className="pt-6">
                  <Lock className="w-6 h-6 text-emerald-400 mb-3" />
                  <h4 className="font-semibold text-foreground mb-2">Secure HTTPS by Default</h4>
                  <p className="text-sm text-muted-foreground">We automatically provision TLS certificates so your traffic is encrypted end-to-end.</p>
                </CardContent>
              </Card>
              <Card className="bg-card/40 border-border/80">
                <CardContent className="pt-6">
                  <Activity className="w-6 h-6 text-blue-600 dark:text-blue-400 mb-3" />
                  <h4 className="font-semibold text-foreground mb-2">Instant & Reliable</h4>
                  <p className="text-sm text-muted-foreground">Connections are established instantly with auto-reconnects built in to handle network drops.</p>
                </CardContent>
              </Card>
              <Card className="bg-card/40 border-border/80">
                <CardContent className="pt-6">
                  <Shield className="w-6 h-6 text-purple-400 mb-3" />
                  <h4 className="font-semibold text-foreground mb-2">Account Security</h4>
                  <p className="text-sm text-muted-foreground">Your connections are securely linked to your account, ensuring only you control your tunnels.</p>
                </CardContent>
              </Card>
              <Card className="bg-card/40 border-border/80">
                <CardContent className="pt-6">
                  <Globe className="w-6 h-6 text-orange-400 mb-3" />
                  <h4 className="font-semibold text-foreground mb-2">Custom Subdomains</h4>
                  <p className="text-sm text-muted-foreground">Use easily identifiable, custom URLs to share your work professionally.</p>
                </CardContent>
              </Card>
            </div>
          </section>

          <section id="examples" className="scroll-mt-32 mb-20">
            <h2 className="text-3xl font-bold mb-6 border-b border-border pb-2">Use Case Examples</h2>
            
            <div className="mb-8">
              <h3 className="text-xl font-semibold mb-3 text-foreground">Sharing a Web Application Demo</h3>
              <p className="text-muted-foreground mb-3">If you are running a React, Vue, or Next.js app on port 3000 and want to share it with a client:</p>
              <div className="bg-background p-4 rounded-lg font-mono text-sm text-muted-foreground border border-border">
                <span className="text-muted-foreground">$ </span>npm run dev <span className="text-muted-foreground"># starts app on port 3000</span><br />
                <span className="text-muted-foreground">$ </span>hushh http 3000
              </div>
              <p className="text-muted-foreground mt-3 text-sm italic">You can now send the `https://[id].hushh.online` link directly to your client. They can view it in their browser instantly.</p>
            </div>

            <div className="mb-8">
              <h3 className="text-xl font-semibold mb-3 text-foreground">Testing Webhooks Locally</h3>
              <p className="text-muted-foreground mb-3">When testing integrations from services like Stripe, GitHub, or Twilio, they need a public URL to send events to. Simply expose your local backend server (e.g., port 8000):</p>
              <div className="bg-background p-4 rounded-lg font-mono text-sm text-muted-foreground border border-border">
                <span className="text-muted-foreground">$ </span>python manage.py runserver 8000<br />
                <span className="text-muted-foreground">$ </span>hushh http 8000
              </div>
              <p className="text-muted-foreground mt-3 text-sm italic">Copy your tunnel URL and paste it into the webhook configuration of Stripe/GitHub. All events will route directly to your local code.</p>
            </div>
          </section>

          <section id="custom-subdomains" className="scroll-mt-32 mb-20">
            <h2 className="text-3xl font-bold mb-6 border-b border-border pb-2">Using Custom Subdomains</h2>
            <p className="text-muted-foreground mb-4">
              By default, Hushh generates a random alphanumeric string for your tunnel (e.g., `a8x91kp3.hushh.online`). 
              For predictable, memorable URLs, you can specify a custom subdomain when starting your tunnel.
            </p>
            <div className="bg-background p-4 rounded-lg font-mono text-sm text-muted-foreground border border-border mb-4">
              <span className="text-muted-foreground">$ </span>hushh http 8080 --subdomain my-awesome-app
              <br /><br />
              <span className="text-emerald-400">✔ Connected</span><br />
              <span className="text-blue-600 dark:text-blue-400">https://my-awesome-app.hushh.online</span> <span className="text-muted-foreground">→</span> http://localhost:8080
            </div>
            <div className="bg-blue-500/10 dark:bg-blue-900/20 border border-blue-500/20 dark:border-blue-900/50 rounded-lg p-4 flex items-start">
              <Book className="w-5 h-5 text-blue-600 dark:text-blue-400 mr-3 shrink-0 mt-0.5" />
              <p className="text-sm text-blue-800 dark:text-blue-200 m-0">
                <strong>Note:</strong> Standard custom subdomains are available on a first-come, first-served basis for the duration of the connection.
              </p>
            </div>
          </section>

          <section id="cli-reference" className="scroll-mt-32 mb-20">
            <h2 className="text-3xl font-bold mb-6 border-b border-border pb-2">CLI Reference</h2>
            <div className="overflow-hidden rounded-xl border border-border bg-card">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-card border-b border-border">
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Command</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Description</th>
                  </tr>
                </thead>
                <tbody className="text-muted-foreground divide-y divide-slate-800/50">
                  <tr className="hover:bg-accent/30 transition">
                    <td className="py-3 px-4 font-mono text-sm text-blue-600 dark:text-blue-300">hushh login</td>
                    <td className="py-3 px-4 text-sm">Sign in to your account.</td>
                  </tr>
                  <tr className="hover:bg-accent/30 transition">
                    <td className="py-3 px-4 font-mono text-sm text-blue-600 dark:text-blue-300">hushh logout</td>
                    <td className="py-3 px-4 text-sm">Sign out of your device.</td>
                  </tr>
                  <tr className="hover:bg-accent/30 transition">
                    <td className="py-3 px-4 font-mono text-sm text-blue-600 dark:text-blue-300">hushh whoami</td>
                    <td className="py-3 px-4 text-sm">View your currently logged in account details.</td>
                  </tr>
                  <tr className="hover:bg-accent/30 transition">
                    <td className="py-3 px-4 font-mono text-sm text-blue-600 dark:text-blue-300">hushh http &lt;port&gt;</td>
                    <td className="py-3 px-4 text-sm">Expose the specified local port to the internet.</td>
                  </tr>
                  <tr className="hover:bg-accent/30 transition">
                    <td className="py-3 px-4 font-mono text-sm text-blue-600 dark:text-blue-300">hushh http &lt;port&gt; --subdomain &lt;name&gt;</td>
                    <td className="py-3 px-4 text-sm">Expose a port using a specific subdomain.</td>
                  </tr>
                  <tr className="hover:bg-accent/30 transition">
                    <td className="py-3 px-4 font-mono text-sm text-blue-600 dark:text-blue-300">hushh status</td>
                    <td className="py-3 px-4 text-sm">View a list of all your active tunnels.</td>
                  </tr>
                  <tr className="hover:bg-accent/30 transition">
                    <td className="py-3 px-4 font-mono text-sm text-blue-600 dark:text-blue-300">hushh stop &lt;subdomain&gt;</td>
                    <td className="py-3 px-4 text-sm">Close a specific running tunnel.</td>
                  </tr>
                  <tr className="hover:bg-accent/30 transition">
                    <td className="py-3 px-4 font-mono text-sm text-blue-600 dark:text-blue-300">hushh version</td>
                    <td className="py-3 px-4 text-sm">Display the current version of the application.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

        </main>
      </div>
      
    </div>
  );
}
