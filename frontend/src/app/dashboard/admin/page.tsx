'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Shield, ShieldAlert, Key, Trash2, CheckCircle2, XCircle } from 'lucide-react';

interface UserInfo {
  id: number;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  max_tunnels: number;
  created_at: string;
}

export default function AdminDashboardPage() {
  const router = useRouter();
  const [users, setUsers] = useState<UserInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUsers = async () => {
    try {
      setIsLoading(true);
      const res = await api.get('/api/users');
      setUsers(res.data);
    } catch (err: any) {
      if (err.response?.status === 403) {
        router.push('/dashboard');
      }
      setError('Failed to fetch users');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleToggleBlock = async (user: UserInfo) => {
    if (user.is_admin) return;
    const action = user.is_active ? 'block' : 'unblock';
    if (!window.confirm(`Are you sure you want to ${action} user ${user.email}?`)) return;
    try {
      await api.patch(`/api/users/${user.id}/status`, { is_active: !user.is_active });
      fetchUsers();
    } catch (err) {
      alert(`Failed to ${action} user`);
    }
  };

  const handleResetPassword = async (user: UserInfo) => {
    if (!window.confirm(`Are you sure you want to reset the password for ${user.email}? This will invalidate their current password immediately.`)) return;
    try {
      const res = await api.post(`/api/users/${user.id}/reset-password`);
      window.alert(`Password reset successfully!\n\nNew Password for ${user.email}:\n${res.data.new_password}\n\nPlease copy and share this with the user securely. This is the only time it will be shown.`);
    } catch (err) {
      alert('Failed to reset password');
    }
  };

  const handleDeleteUser = async (user: UserInfo) => {
    if (user.is_admin) return;
    if (!window.confirm(`WARNING: Are you absolutely sure you want to permanently DELETE user ${user.email}? This action cannot be undone and will destroy all their active tunnels.`)) return;
    try {
      await api.delete(`/api/users/${user.id}`);
      fetchUsers();
    } catch (err) {
      alert('Failed to delete user');
    }
  };

  if (isLoading) return <div className="text-slate-400">Loading admin data...</div>;
  if (error) return <div className="text-red-400">{error}</div>;

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center">
          <Shield className="w-8 h-8 text-blue-500 mr-3" />
          Admin Dashboard
        </h1>
        <p className="mt-2 text-sm text-slate-400">
          Manage platform users, reset passwords, and enforce security policies.
        </p>
      </div>

      <Card className="bg-slate-900 border-slate-800">
        <CardHeader>
          <CardTitle>Registered Users</CardTitle>
          <CardDescription>A complete list of all users on the platform.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400">
                  <th className="pb-3 pr-4 font-medium">ID</th>
                  <th className="pb-3 pr-4 font-medium">Email</th>
                  <th className="pb-3 pr-4 font-medium">Joined</th>
                  <th className="pb-3 pr-4 font-medium">Status</th>
                  <th className="pb-3 pr-4 font-medium">Admin</th>
                  <th className="pb-3 pr-4 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-800/30 transition">
                    <td className="py-4 pr-4 font-mono text-slate-400">{u.id}</td>
                    <td className="py-4 pr-4 text-slate-200">{u.email}</td>
                    <td className="py-4 pr-4 text-slate-400">{new Date(u.created_at).toLocaleDateString()}</td>
                    <td className="py-4 pr-4">
                      {u.is_active ? (
                        <span className="inline-flex items-center text-emerald-400 text-xs px-2 py-1 bg-emerald-400/10 rounded-full">
                          <CheckCircle2 className="w-3 h-3 mr-1" /> Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center text-red-400 text-xs px-2 py-1 bg-red-400/10 rounded-full">
                          <XCircle className="w-3 h-3 mr-1" /> Blocked
                        </span>
                      )}
                    </td>
                    <td className="py-4 pr-4">
                      {u.is_admin ? (
                        <span className="inline-flex items-center text-blue-400 text-xs px-2 py-1 bg-blue-400/10 rounded-full">
                          Admin
                        </span>
                      ) : (
                        <span className="text-slate-500 text-xs">User</span>
                      )}
                    </td>
                    <td className="py-4 pr-4 text-right space-x-2">
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="bg-transparent border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white"
                        onClick={() => handleResetPassword(u)}
                        title="Reset Password"
                      >
                        <Key className="w-4 h-4" />
                      </Button>
                      
                      {!u.is_admin && (
                        <>
                          <Button 
                            variant="outline" 
                            size="sm" 
                            className={`bg-transparent border-slate-700 hover:bg-slate-800 ${
                              u.is_active ? 'text-amber-400 hover:text-amber-300' : 'text-emerald-400 hover:text-emerald-300'
                            }`}
                            onClick={() => handleToggleBlock(u)}
                            title={u.is_active ? "Block User" : "Unblock User"}
                          >
                            <ShieldAlert className="w-4 h-4" />
                          </Button>
                          <Button 
                            variant="outline" 
                            size="sm" 
                            className="bg-transparent border-slate-700 text-red-400 hover:bg-red-900/30 hover:text-red-300"
                            onClick={() => handleDeleteUser(u)}
                            title="Delete User"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
                {users.length === 0 && (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-400">
                      No users found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
