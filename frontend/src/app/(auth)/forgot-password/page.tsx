'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function ForgotPasswordPage() {
  return (
    <div>
      <h2 className="text-center text-2xl font-bold leading-9 tracking-tight text-white mb-4">
        Reset your password
      </h2>
      <p className="text-center text-sm text-slate-400 mb-8">
        Enter your email address and we will send you a link to reset your password.
      </p>

      <form className="space-y-6" onSubmit={(e) => e.preventDefault()}>
        <div>
          <Label htmlFor="email">Email address</Label>
          <div className="mt-2">
            <Input
              id="email"
              type="email"
              className="bg-slate-950 border-slate-800"
              required
            />
          </div>
        </div>

        <Button type="button" className="w-full bg-blue-600 hover:bg-blue-700" onClick={() => alert('Password reset emails are not configured.')}>
          Send reset link
        </Button>
      </form>

      <p className="mt-10 text-center text-sm text-slate-400">
        Remember your password?{' '}
        <Link href="/login" className="font-semibold leading-6 text-blue-500 hover:text-blue-400">
          Back to login
        </Link>
      </p>
    </div>
  );
}
