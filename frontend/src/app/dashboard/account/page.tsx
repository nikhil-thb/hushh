'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { User as UserIcon, Calendar, Lock, Trash2 } from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';

export default function AccountPage() {
  const { data: user, isLoading } = useQuery({
    queryKey: ['whoami'],
    queryFn: async () => {
      const res = await api.get('/auth/whoami');
      return res.data;
    },
  });

  return (
    <div className="space-y-6 max-w-3xl">
      <h1 className="text-3xl font-bold tracking-tight">Account Settings</h1>
      
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription className="text-slate-400">Your account information</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-slate-300">Email Address</Label>
              <div className="flex items-center space-x-2 bg-slate-950 p-2 rounded-md border border-slate-800 text-slate-400">
                <UserIcon className="w-4 h-4" />
                <span className="text-sm">{isLoading ? 'Loading...' : user?.email}</span>
              </div>
            </div>
            
            <div className="space-y-2">
              <Label className="text-slate-300">Member Since</Label>
              <div className="flex items-center space-x-2 bg-slate-950 p-2 rounded-md border border-slate-800 text-slate-400">
                <Calendar className="w-4 h-4" />
                <span className="text-sm">
                  {isLoading ? 'Loading...' : new Date(user?.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-slate-900 border-slate-800">
        <CardHeader>
          <CardTitle>Security</CardTitle>
          <CardDescription className="text-slate-400">Update your password</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="current-password">Current Password</Label>
            <Input id="current-password" type="password" className="bg-slate-950 border-slate-800" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="new-password">New Password</Label>
            <Input id="new-password" type="password" className="bg-slate-950 border-slate-800" />
          </div>
          <Button className="bg-blue-600 hover:bg-blue-700">Update Password</Button>
        </CardContent>
      </Card>

      <Card className="bg-slate-900 border-red-900/50">
        <CardHeader>
          <CardTitle className="text-red-500">Danger Zone</CardTitle>
          <CardDescription className="text-slate-400">Permanently delete your account and all associated tunnels.</CardDescription>
        </CardHeader>
        <CardContent>
          <Dialog>
            <DialogTrigger render={<Button variant="destructive" className="bg-red-600/10 text-red-500 hover:bg-red-600/20 border border-red-500/20" />}>
              <Trash2 className="w-4 h-4 mr-2" />
              Delete Account
            </DialogTrigger>
            <DialogContent className="bg-slate-900 border-slate-800 text-slate-50">
              <DialogHeader>
                <DialogTitle className="text-red-500">Are you absolutely sure?</DialogTitle>
                <DialogDescription className="text-slate-400">
                  This action cannot be undone. This will permanently delete your account, 
                  terminate all active tunnels, and remove your data from our servers.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter className="mt-6">
                <Button variant="outline" className="border-slate-800 bg-slate-900 text-slate-300">Cancel</Button>
                <Button variant="destructive" className="bg-red-600 hover:bg-red-700 text-white" onClick={() => alert('Not implemented')}>
                  Yes, delete my account
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </CardContent>
      </Card>
    </div>
  );
}
