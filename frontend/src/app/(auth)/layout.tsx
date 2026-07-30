import Link from 'next/link';
import { ThemeToggle } from '@/components/ThemeToggle';

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-background relative">
      <div className="absolute top-4 right-4 sm:top-8 sm:right-8">
        <ThemeToggle />
      </div>
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <Link href="/" className="flex items-center justify-center space-x-2">
          <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center font-bold text-xl text-primary-foreground">H</div>
          <span className="font-bold text-2xl tracking-tight text-foreground">Hushh</span>
        </Link>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-card backdrop-blur-xl py-8 px-4 shadow sm:rounded-2xl border border-border sm:px-10">
          {children}
        </div>
      </div>
    </div>
  );
}
