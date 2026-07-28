'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Search, RefreshCw, PowerOff, Eye } from 'lucide-react';
import { useState } from 'react';

type TunnelInfo = {
  subdomain: string;
  tunnel_url: string;
  user_id: number;
  local_port: number;
  client_version: string;
  created_at: string;
  last_seen_at: string;
  pending_requests: int;
};

export default function TunnelsPage() {
  const [searchTerm, setSearchTerm] = useState('');

  const { data: tunnels, isLoading, refetch } = useQuery({
    queryKey: ['tunnels'],
    queryFn: async () => {
      const res = await api.get<TunnelInfo[]>('/api/tunnels');
      return res.data;
    },
    refetchInterval: 5000,
  });

  const filteredTunnels = tunnels?.filter(t => 
    t.subdomain.includes(searchTerm) || t.tunnel_url.includes(searchTerm)
  );

  const disconnectTunnel = async (subdomain: string) => {
    if (confirm(`Disconnect tunnel ${subdomain}?`)) {
      try {
        await api.delete(`/api/tunnels/${subdomain}`);
        refetch();
      } catch (e) {
        console.error('Failed to disconnect');
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-3xl font-bold tracking-tight">Active Tunnels</h1>
        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-500" />
            <Input
              placeholder="Search tunnels..."
              className="pl-9 bg-slate-900 border-slate-800"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <Button variant="outline" size="icon" onClick={() => refetch()} className="border-slate-800 bg-slate-900 text-slate-300 hover:text-white">
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
        <Table>
          <TableHeader className="bg-slate-950/50">
            <TableRow className="border-slate-800 hover:bg-transparent">
              <TableHead>Status</TableHead>
              <TableHead>URL / Subdomain</TableHead>
              <TableHead>Target Port</TableHead>
              <TableHead>Started</TableHead>
              <TableHead>Pending Reqs</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow className="border-slate-800 hover:bg-slate-900/50">
                <TableCell colSpan={6} className="text-center py-8 text-slate-500">Loading tunnels...</TableCell>
              </TableRow>
            ) : filteredTunnels?.length === 0 ? (
              <TableRow className="border-slate-800 hover:bg-slate-900/50">
                <TableCell colSpan={6} className="text-center py-8 text-slate-500">
                  No active tunnels found. Run `hushh http 3000` to start one.
                </TableCell>
              </TableRow>
            ) : (
              filteredTunnels?.map((tunnel) => (
                <TableRow key={tunnel.subdomain} className="border-slate-800 hover:bg-slate-800/50">
                  <TableCell>
                    <Badge variant="outline" className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20">
                      Online
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="font-medium text-slate-200">{tunnel.tunnel_url}</div>
                    <div className="text-xs text-slate-500">{tunnel.subdomain}</div>
                  </TableCell>
                  <TableCell>
                    <span className="font-mono text-slate-300">{tunnel.local_port}</span>
                  </TableCell>
                  <TableCell className="text-slate-400">
                    {new Date(tunnel.created_at).toLocaleString()}
                  </TableCell>
                  <TableCell className="text-slate-400">
                    {tunnel.pending_requests}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end space-x-2">
                      <Link href={`/dashboard/tunnels/${tunnel.subdomain}`}>
                        <Button variant="ghost" size="icon" className="text-slate-400 hover:text-white" title="View details">
                          <Eye className="h-4 w-4" />
                        </Button>
                      </Link>
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                        title="Disconnect"
                        onClick={() => disconnectTunnel(tunnel.subdomain)}
                      >
                        <PowerOff className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
