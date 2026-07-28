import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Terminal, Download } from 'lucide-react';

export default function DownloadsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Downloads</h1>
        <p className="text-slate-400 mt-2">Install the Hushh CLI client for your platform.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Linux */}
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Terminal className="w-5 h-5 text-emerald-500" />
              <span>Linux</span>
            </CardTitle>
            <CardDescription className="text-slate-400">Install via Python PIP</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-slate-950 p-3 rounded-md border border-slate-800 font-mono text-sm text-slate-300">
              <span className="text-blue-400">$</span> pip install hushh-tunnel
            </div>
            <div className="text-sm text-slate-400 space-y-1">
              <p>Latest Version: v0.1.0</p>
              <p><a href="#" className="text-blue-500 hover:underline">Release Notes</a></p>
              <p><a href="https://github.com/nikhil-v/hushh/releases" target="_blank" className="text-blue-500 hover:underline">GitHub Releases</a></p>
            </div>
          </CardContent>
        </Card>

        {/* macOS */}
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Terminal className="w-5 h-5 text-blue-500" />
              <span>macOS</span>
            </CardTitle>
            <CardDescription className="text-slate-400">Install via Python PIP</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-slate-950 p-3 rounded-md border border-slate-800 font-mono text-sm text-slate-300">
              <span className="text-blue-400">$</span> pip install hushh-tunnel
            </div>
            <div className="text-sm text-slate-400 space-y-1">
              <p>Latest Version: v0.1.0</p>
              <p><a href="#" className="text-blue-500 hover:underline">Release Notes</a></p>
              <p><a href="https://github.com/nikhil-v/hushh/releases" target="_blank" className="text-blue-500 hover:underline">GitHub Releases</a></p>
            </div>
          </CardContent>
        </Card>

        {/* Windows */}
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Terminal className="w-5 h-5 text-purple-500" />
              <span>Windows</span>
            </CardTitle>
            <CardDescription className="text-slate-400">Install via Python PIP</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-slate-950 p-3 rounded-md border border-slate-800 font-mono text-sm text-slate-300">
              <span className="text-blue-400">$</span> pip install hushh-tunnel
            </div>
            <div className="text-sm text-slate-400 space-y-1">
              <p>Latest Version: v0.1.0</p>
              <p><a href="#" className="text-blue-500 hover:underline">Release Notes</a></p>
              <p><a href="https://github.com/nikhil-v/hushh/releases" target="_blank" className="text-blue-500 hover:underline">GitHub Releases</a></p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
