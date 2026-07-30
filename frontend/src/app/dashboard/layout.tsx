'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { 
  LayoutDashboard, 
  Network, 
  Key, 
  Download, 
  User as UserIcon, 
  LogOut,
  Menu,
  Shield
} from 'lucide-react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from '@/components/ThemeToggle';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Tunnels', href: '/dashboard/tunnels', icon: Network },
  { name: 'API Keys', href: '/dashboard/api-keys', icon: Key },
  { name: 'Downloads', href: '/dashboard/downloads', icon: Download },
  { name: 'Account', href: '/dashboard/account', icon: UserIcon },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
    } else {
      api.get('/auth/whoami')
        .then(res => setIsAdmin(res.data.is_admin))
        .catch(() => {});
    }
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('api_key');
    router.push('/login');
  };

  return (
    <div className="flex h-screen bg-background text-foreground">
      {/* Desktop Sidebar */}
      <div className="hidden md:flex md:w-64 md:flex-col bg-card border-r border-border">
        <div className="flex flex-col flex-grow pt-5 overflow-y-auto">
          <div className="flex items-center justify-between px-4">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center font-bold text-lg text-primary-foreground">H</div>
              <span className="font-semibold text-lg tracking-tight">Hushh Tunnel</span>
            </div>
          </div>
          <div className="mt-8 flex-grow flex flex-col">
            <nav className="flex-1 px-2 space-y-1">
              {navigation.map((item) => {
                const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md ${
                      isActive
                        ? 'bg-accent text-accent-foreground'
                        : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                    }`}
                  >
                    <item.icon
                      className={`mr-3 flex-shrink-0 h-5 w-5 ${
                        isActive ? 'text-primary' : 'text-muted-foreground group-hover:text-accent-foreground'
                      }`}
                      aria-hidden="true"
                    />
                    {item.name}
                  </Link>
                );
              })}
              {isAdmin && (
                <Link
                  href="/dashboard/admin"
                  className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md ${
                    pathname === '/dashboard/admin' || pathname.startsWith('/dashboard/admin/')
                      ? 'bg-accent text-accent-foreground'
                      : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                  }`}
                >
                  <Shield
                    className={`mr-3 flex-shrink-0 h-5 w-5 ${
                      pathname === '/dashboard/admin' || pathname.startsWith('/dashboard/admin/') ? 'text-primary' : 'text-muted-foreground group-hover:text-accent-foreground'
                    }`}
                    aria-hidden="true"
                  />
                  Admin
                </Link>
              )}
            </nav>
          </div>
          <div className="flex-shrink-0 flex flex-col border-t border-border p-4 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-muted-foreground">Theme</span>
              <ThemeToggle />
            </div>
            <button
              onClick={handleLogout}
              className="flex-shrink-0 w-full group block text-muted-foreground hover:text-foreground transition flex items-center"
            >
              <LogOut className="inline-block h-5 w-5 mr-2" />
              <span className="text-sm font-medium">Logout</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex flex-col flex-1 w-0 overflow-hidden">
        <div className="md:hidden flex items-center justify-between p-2 border-b border-border bg-card">
          <Button
            variant="ghost"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          >
            <Menu className="h-6 w-6" aria-hidden="true" />
          </Button>
          <ThemeToggle />
        </div>
        
        <main className="flex-1 relative z-0 overflow-y-auto focus:outline-none">
          <div className="py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
