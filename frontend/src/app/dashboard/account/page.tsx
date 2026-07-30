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
      
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription className="text-muted-foreground">Your account information</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-muted-foreground">Email Address</Label>
              <div className="flex items-center space-x-2 bg-background p-2 rounded-md border border-border text-muted-foreground">
                <UserIcon className="w-4 h-4" />
                <span className="text-sm">{isLoading ? 'Loading...' : user?.email}</span>
              </div>
            </div>
            
            <div className="space-y-2">
              <Label className="text-muted-foreground">Member Since</Label>
              <div className="flex items-center space-x-2 bg-background p-2 rounded-md border border-border text-muted-foreground">
                <Calendar className="w-4 h-4" />
                <span className="text-sm">
                  {isLoading ? 'Loading...' : new Date(user?.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle>Security</CardTitle>
          <CardDescription className="text-muted-foreground">Update your password</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="current-password">Current Password</Label>
            <Input id="current-password" type="password" className="bg-background border-border" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="new-password">New Password</Label>
            <Input id="new-password" type="password" className="bg-background border-border" />
          </div>
          <Button className="bg-primary hover:bg-primary/90">Update Password</Button>
        </CardContent>
      </Card>

      <Card className="bg-card border-red-900/50">
        <CardHeader>
          <CardTitle className="text-red-500">Danger Zone</CardTitle>
          <CardDescription className="text-muted-foreground">Permanently delete your account and all associated tunnels.</CardDescription>
        </CardHeader>
        <CardContent>
          <Dialog>
            <DialogTrigger render={<Button variant="destructive" className="bg-red-600/10 text-red-500 hover:bg-red-600/20 border border-red-500/20" />}>
              <Trash2 className="w-4 h-4 mr-2" />
              Delete Account
            </DialogTrigger>
            <DialogContent className="bg-card border-border text-foreground">
              <DialogHeader>
                <DialogTitle className="text-red-500">Are you absolutely sure?</DialogTitle>
                <DialogDescription className="text-muted-foreground">
                  This action cannot be undone. This will permanently delete your account, 
                  terminate all active tunnels, and remove your data from our servers.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter className="mt-6">
                <Button variant="outline" className="border-border bg-card text-muted-foreground">Cancel</Button>
                <Button variant="destructive" className="bg-red-600 hover:bg-red-700 text-foreground" onClick={() => alert('Not implemented')}>
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
