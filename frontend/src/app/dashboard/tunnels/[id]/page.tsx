'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { ArrowLeft, Copy, RefreshCw, PowerOff, Globe, Clock, Activity, HardDriveDownload, HardDriveUpload } from 'lucide-react';
import Link from 'next/link';

export default function TunnelDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const { data: tunnel, isLoading, refetch: refetchTunnel } = useQuery({
    queryKey: ['tunnel', id],
    queryFn: async () => {
      const res = await api.get(`/api/tunnels/${id}`);
      return res.data;
    },
    refetchInterval: 5000,
  });

  // Fetch request logs from the new endpoint
  const { data: logs, refetch: refetchLogs } = useQuery({
    queryKey: ['tunnel-logs', id],
    queryFn: async () => {
      const res = await api.get(`/api/dashboard/request-logs/${id}`);
      return res.data;
    },
    refetchInterval: 5000,
  });

  const copyUrl = () => {
    if (tunnel) {
      navigator.clipboard.writeText(tunnel.tunnel_url);
      alert('URL copied!');
    }
  };

  const disconnect = async () => {
    if (confirm('Are you sure you want to disconnect this tunnel?')) {
      await api.delete(`/api/tunnels/${id}`);
      router.push('/dashboard/tunnels');
    }
  };

  if (isLoading) {
    return <div className="text-muted-foreground">Loading tunnel details...</div>;
  }

  if (!tunnel) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold mb-2">Tunnel not found</h2>
        <p className="text-muted-foreground mb-6">This tunnel may have been disconnected or doesn't exist.</p>
        <Link href="/dashboard/tunnels">
          <Button variant="outline">Back to Tunnels</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4 mb-2">
        <Link href="/dashboard/tunnels" className="text-muted-foreground hover:text-foreground transition">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <h1 className="text-2xl font-bold tracking-tight flex items-center space-x-3">
          <span>{tunnel.subdomain}</span>
          <Badge variant="outline" className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20">Online</Badge>
        </h1>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <Button onClick={copyUrl} variant="secondary" className="bg-accent hover:bg-slate-700">
          <Copy className="w-4 h-4 mr-2" /> Copy URL
        </Button>
        <Button onClick={() => { refetchTunnel(); refetchLogs(); }} variant="outline" className="border-border bg-card text-muted-foreground">
          <RefreshCw className="w-4 h-4 mr-2" /> Refresh
        </Button>
        <Button onClick={disconnect} variant="destructive" className="bg-red-600 hover:bg-red-700 text-foreground">
          <PowerOff className="w-4 h-4 mr-2" /> Disconnect
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-card border-border">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Tunnel URL</CardTitle>
            <Globe className="w-4 h-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-lg font-semibold truncate" title={tunnel.tunnel_url}>{tunnel.tunnel_url}</div>
          </CardContent>
        </Card>
        
        <Card className="bg-card border-border">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Target</CardTitle>
            <Activity className="w-4 h-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-lg font-semibold">localhost:{tunnel.local_port}</div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Started At</CardTitle>
            <Clock className="w-4 h-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-sm font-medium">{new Date(tunnel.created_at).toLocaleString()}</div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Pending Requests</CardTitle>
            <RefreshCw className="w-4 h-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{tunnel.pending_requests}</div>
          </CardContent>
        </Card>
      </div>

      <div className="mt-8">
        <h2 className="text-xl font-semibold mb-4">Latest Requests</h2>
        <div className="bg-card border border-border rounded-lg overflow-hidden">
          <Table>
            <TableHeader className="bg-background/50">
              <TableRow className="border-border hover:bg-transparent">
                <TableHead>Time</TableHead>
                <TableHead>Method</TableHead>
                <TableHead>Path</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Duration</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs?.length === 0 ? (
                <TableRow className="border-border hover:bg-card">
                  <TableCell colSpan={5} className="text-center py-8 text-foreground0">
                    No requests recorded yet.
                  </TableCell>
                </TableRow>
              ) : (
                logs?.map((log: any, i: number) => (
                  <TableRow key={i} className="border-border hover:bg-accent/50">
                    <TableCell className="text-muted-foreground">{new Date(log.created_at).toLocaleTimeString()}</TableCell>
                    <TableCell className="font-mono text-blue-400">{log.method}</TableCell>
                    <TableCell className="text-muted-foreground">{log.path}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className={log.status < 400 ? 'text-emerald-400 border-emerald-400/20' : 'text-red-400 border-red-400/20'}>
                        {log.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{log.duration}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  );
}
