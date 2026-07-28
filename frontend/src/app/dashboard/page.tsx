'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Activity, Radio, WifiOff, Copy } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

export default function DashboardHome() {
  const [apiKey, setApiKey] = useState<string>('');
  
  useEffect(() => {
    setApiKey(localStorage.getItem('api_key') || 'Not found');
  }, []);

  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const res = await api.get('/api/dashboard/stats');
      return res.data;
    },
    refetchInterval: 5000,
  });

  const copyApiKey = () => {
    navigator.clipboard.writeText(apiKey);
    alert('API Key copied to clipboard!'); // Need to use Shadcn toast later
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-400">Active Tunnels</CardTitle>
            <Radio className="w-4 h-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            {isLoading ? <Skeleton className="h-8 w-20 bg-slate-800" /> : (
              <div className="text-3xl font-bold">{stats?.active_tunnels || 0}</div>
            )}
          </CardContent>
        </Card>

        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-400">Offline Tunnels</CardTitle>
            <WifiOff className="w-4 h-4 text-slate-500" />
          </CardHeader>
          <CardContent>
            {isLoading ? <Skeleton className="h-8 w-20 bg-slate-800" /> : (
              <div className="text-3xl font-bold">{stats?.offline_tunnels || 0}</div>
            )}
          </CardContent>
        </Card>

        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-400">Total Requests</CardTitle>
            <Activity className="w-4 h-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            {isLoading ? <Skeleton className="h-8 w-20 bg-slate-800" /> : (
              <div className="text-3xl font-bold">{stats?.total_requests || 0}</div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* API Key Card */}
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
            <CardTitle>Your API Key</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-slate-400">
              Use this key to authenticate your CLI client. Keep it secret.
            </p>
            <div className="flex items-center space-x-2">
              <code className="flex-1 p-3 bg-slate-950 border border-slate-800 rounded-md font-mono text-sm text-slate-300 truncate">
                {apiKey ? 'hushh_••••••••••••••••••••••••' : 'Loading...'}
              </code>
              <Button onClick={copyApiKey} variant="secondary" className="bg-slate-800 hover:bg-slate-700">
                <Copy className="w-4 h-4 mr-2" />
                Copy
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* CLI Commands Card */}
        <Card className="bg-slate-900 border-slate-800 lg:col-span-2">
          <CardHeader>
            <CardTitle>CLI Commands</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              
              {/* Install */}
              <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 font-mono text-sm text-slate-300">
                <span className="text-slate-500"># Install the CLI</span>
                <div className="flex items-center space-x-2 mt-2">
                  <code className="flex-1 px-3 py-2 bg-slate-900 rounded border border-slate-700 truncate">
                    pip install hushh-tunnel
                  </code>
                  <Button 
                    onClick={() => { navigator.clipboard.writeText(`pip install hushh-tunnel`); alert('Command copied!'); }} 
                    variant="secondary" size="sm" className="bg-slate-800 hover:bg-slate-700"
                  >
                    <Copy className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Login */}
              <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 font-mono text-sm text-slate-300">
                <span className="text-slate-500"># Login directly with your API Key</span>
                <div className="flex items-center space-x-2 mt-2">
                  <code className="flex-1 px-3 py-2 bg-slate-900 rounded border border-slate-700 truncate">
                    hushh login {apiKey ? apiKey : '...'}
                  </code>
                  <Button 
                    onClick={() => { navigator.clipboard.writeText(`hushh login ${apiKey}`); alert('Command copied!'); }} 
                    variant="secondary" size="sm" className="bg-slate-800 hover:bg-slate-700"
                  >
                    <Copy className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Basic Tunnel */}
              <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 font-mono text-sm text-slate-300">
                <span className="text-slate-500"># Start a tunnel for local port 3000</span>
                <div className="flex items-center space-x-2 mt-2">
                  <code className="flex-1 px-3 py-2 bg-slate-900 rounded border border-slate-700 truncate">
                    hushh http 3000
                  </code>
                  <Button 
                    onClick={() => { navigator.clipboard.writeText(`hushh http 3000`); alert('Command copied!'); }} 
                    variant="secondary" size="sm" className="bg-slate-800 hover:bg-slate-700"
                  >
                    <Copy className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Custom Subdomain */}
              <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 font-mono text-sm text-slate-300">
                <span className="text-slate-500"># Request a custom subdomain</span>
                <div className="flex items-center space-x-2 mt-2">
                  <code className="flex-1 px-3 py-2 bg-slate-900 rounded border border-slate-700 truncate">
                    hushh http 8080 --subdomain myapi
                  </code>
                  <Button 
                    onClick={() => { navigator.clipboard.writeText(`hushh http 8080 --subdomain myapi`); alert('Command copied!'); }} 
                    variant="secondary" size="sm" className="bg-slate-800 hover:bg-slate-700"
                  >
                    <Copy className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Status */}
              <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 font-mono text-sm text-slate-300">
                <span className="text-slate-500"># View active tunnels</span>
                <div className="flex items-center space-x-2 mt-2">
                  <code className="flex-1 px-3 py-2 bg-slate-900 rounded border border-slate-700 truncate">
                    hushh status
                  </code>
                  <Button 
                    onClick={() => { navigator.clipboard.writeText(`hushh status`); alert('Command copied!'); }} 
                    variant="secondary" size="sm" className="bg-slate-800 hover:bg-slate-700"
                  >
                    <Copy className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Stop Tunnel */}
              <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 font-mono text-sm text-slate-300">
                <span className="text-slate-500"># Stop a specific tunnel</span>
                <div className="flex items-center space-x-2 mt-2">
                  <code className="flex-1 px-3 py-2 bg-slate-900 rounded border border-slate-700 truncate">
                    hushh stop &lt;subdomain&gt;
                  </code>
                  <Button 
                    onClick={() => { navigator.clipboard.writeText(`hushh stop <subdomain>`); alert('Command copied!'); }} 
                    variant="secondary" size="sm" className="bg-slate-800 hover:bg-slate-700"
                  >
                    <Copy className="w-4 h-4" />
                  </Button>
                </div>
              </div>

            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
