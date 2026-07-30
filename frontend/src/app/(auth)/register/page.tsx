'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RefreshCw } from 'lucide-react';

const registerSchema = z.object({
  email: z.string().email('Please enter a valid email'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirmPassword: z.string(),
  captcha_answer: z.string().min(1, 'Please solve the captcha'),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

type RegisterForm = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [captchaToken, setCaptchaToken] = useState<string>('');
  const [captchaQuestion, setCaptchaQuestion] = useState<string>('Loading...');

  const fetchCaptcha = async () => {
    try {
      const res = await api.get('/auth/captcha');
      setCaptchaToken(res.data.token);
      setCaptchaQuestion(res.data.question);
    } catch (err) {
      console.error('Failed to load captcha', err);
    }
  };

  useEffect(() => {
    fetchCaptcha();
  }, []);
  
  const {
    register,
    handleSubmit,
    resetField,
    formState: { errors, isSubmitting },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterForm) => {
    try {
      setError(null);
      await api.post('/auth/register', {
        email: data.email,
        password: data.password,
        captcha_token: captchaToken,
        captcha_answer: data.captcha_answer,
      });
      // Redirect to login after successful registration
      router.push('/login?registered=true');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'An error occurred during registration');
      fetchCaptcha();
      resetField('captcha_answer');
    }
  };

  return (
    <div>
      <h2 className="text-center text-2xl font-bold leading-9 tracking-tight text-white mb-8">
        Create a new account
      </h2>

      <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-md text-sm">
            {error}
          </div>
        )}

        <div>
          <Label htmlFor="email">Email address</Label>
          <div className="mt-2">
            <Input
              id="email"
              type="email"
              {...register('email')}
              className="bg-slate-950 border-slate-800"
            />
            {errors.email && (
              <p className="mt-1 text-sm text-red-400">{errors.email.message}</p>
            )}
          </div>
        </div>

        <div>
          <Label htmlFor="password">Password</Label>
          <div className="mt-2">
            <Input
              id="password"
              type="password"
              {...register('password')}
              className="bg-slate-950 border-slate-800"
            />
            {errors.password && (
              <p className="mt-1 text-sm text-red-400">{errors.password.message}</p>
            )}
          </div>
        </div>

        <div>
          <Label htmlFor="confirmPassword">Confirm Password</Label>
          <div className="mt-2">
            <Input
              id="confirmPassword"
              type="password"
              {...register('confirmPassword')}
              className="bg-slate-950 border-slate-800"
            />
            {errors.confirmPassword && (
              <p className="mt-1 text-sm text-red-400">{errors.confirmPassword.message}</p>
            )}
          </div>
        </div>

        <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <Label htmlFor="captcha_answer" className="text-slate-300">Security Check</Label>
            <button type="button" onClick={fetchCaptcha} className="text-slate-400 hover:text-white" title="Refresh Captcha">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
          <div className="flex items-center space-x-3">
            <div className="bg-slate-950 border border-slate-700 px-3 py-2 rounded-md font-mono text-sm tracking-widest text-emerald-400 w-1/2 text-center select-none flex items-center justify-center h-10">
              {captchaQuestion}
            </div>
            <Input
              id="captcha_answer"
              type="text"
              placeholder="Answer"
              {...register('captcha_answer')}
              className="bg-slate-950 border-slate-800 w-1/2"
              autoComplete="off"
            />
          </div>
          {errors.captcha_answer && (
            <p className="mt-1 text-sm text-red-400">{errors.captcha_answer.message}</p>
          )}
        </div>

        <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700" disabled={isSubmitting}>
          {isSubmitting ? 'Creating account...' : 'Create account'}
        </Button>
      </form>

      <p className="mt-10 text-center text-sm text-slate-400">
        Already have an account?{' '}
        <Link href="/login" className="font-semibold leading-6 text-blue-500 hover:text-blue-400">
          Sign in
        </Link>
      </p>
    </div>
  );
}
