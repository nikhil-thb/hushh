'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import Link from 'next/link';
import { api } from '@/lib/api';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

const emailSchema = z.object({
  email: z.string().email('Please enter a valid email'),
});

const otpSchema = z.object({
  otp: z.string().length(6, 'OTP must be 6 digits'),
});

const passwordSchema = z.object({
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

export default function ForgotPasswordPage() {
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [error, setError] = useState<string | null>(null);
  
  // Stored state between steps
  const [email, setEmail] = useState('');
  const [verificationToken, setVerificationToken] = useState('');

  const {
    register: registerEmail,
    handleSubmit: handleSubmitEmail,
    watch: watchEmail,
    formState: { errors: emailErrors, isSubmitting: isSubmittingEmail, isValid: isEmailValid },
  } = useForm<z.infer<typeof emailSchema>>({ 
    resolver: zodResolver(emailSchema),
    mode: 'onChange',
  });

  const currentEmailValue = watchEmail('email');
  const isSendDisabled = isSubmittingEmail || !isEmailValid || !currentEmailValue;

  const {
    register: registerOtp,
    handleSubmit: handleSubmitOtp,
    formState: { errors: otpErrors, isSubmitting: isSubmittingOtp },
  } = useForm<z.infer<typeof otpSchema>>({ resolver: zodResolver(otpSchema) });

  const {
    register: registerPassword,
    handleSubmit: handleSubmitPassword,
    formState: { errors: passwordErrors, isSubmitting: isSubmittingPassword },
  } = useForm<z.infer<typeof passwordSchema>>({ resolver: zodResolver(passwordSchema) });

  const onEmailSubmit = async (data: z.infer<typeof emailSchema>) => {
    try {
      setError(null);
      await api.post('/auth/request-otp', {
        email: data.email,
        purpose: 'reset_password',
      });
      setEmail(data.email);
      setStep(2);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send OTP');
    }
  };

  const onOtpSubmit = async (data: z.infer<typeof otpSchema>) => {
    try {
      setError(null);
      const res = await api.post('/auth/verify-otp', {
        email,
        otp: data.otp,
        purpose: 'reset_password',
      });
      setVerificationToken(res.data.verification_token);
      setStep(3);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid or expired OTP');
    }
  };

  const onPasswordSubmit = async (data: z.infer<typeof passwordSchema>) => {
    try {
      setError(null);
      await api.post('/auth/reset-password', {
        email,
        new_password: data.password,
        verification_token: verificationToken,
      });
      setStep(4); // Success step
    } catch (err: any) {
      setError(err.response?.data?.detail || 'An error occurred during password reset');
    }
  };

  return (
    <div>
      <h2 className="text-center text-2xl font-bold leading-9 tracking-tight text-white mb-4">
        {step === 4 ? 'Password Reset Successful' : 'Reset your password'}
      </h2>
      
      {step === 1 && (
        <p className="text-center text-sm text-slate-400 mb-8">
          Enter your email address and we will send you a verification code to reset your password.
        </p>
      )}

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-md text-sm mb-6">
          {error}
        </div>
      )}

      {step === 1 && (
        <form className="space-y-6" onSubmit={handleSubmitEmail(onEmailSubmit)}>
          <div>
            <Label htmlFor="email">Email address</Label>
            <div className="mt-2">
              <Input
                id="email"
                type="email"
                {...registerEmail('email')}
                className="bg-slate-950 border-slate-800"
              />
              {emailErrors.email && (
                <p className="mt-1 text-sm text-red-400">{emailErrors.email.message}</p>
              )}
            </div>
          </div>
          <Button 
            type="submit" 
            className={`w-full ${isSendDisabled ? 'bg-slate-800 text-slate-500' : 'bg-blue-600 hover:bg-blue-700 text-white'}`}
            disabled={isSendDisabled}
          >
            {isSubmittingEmail ? 'Sending...' : 'Send Verification Code'}
          </Button>
        </form>
      )}

      {step === 2 && (
        <form className="space-y-6" onSubmit={handleSubmitOtp(onOtpSubmit)}>
          <p className="text-sm text-slate-400 text-center mb-4">
            Enter the 6-digit verification code sent to {email}
          </p>
          <div>
            <Label htmlFor="otp">Verification Code</Label>
            <div className="mt-2">
              <Input
                id="otp"
                type="text"
                placeholder="123456"
                {...registerOtp('otp')}
                className="bg-slate-950 border-slate-800 font-mono text-center tracking-[0.5em]"
                maxLength={6}
                autoComplete="off"
              />
              {otpErrors.otp && (
                <p className="mt-1 text-sm text-red-400">{otpErrors.otp.message}</p>
              )}
            </div>
          </div>
          <div className="flex gap-4">
             <Button type="button" variant="outline" className="w-1/3 border-slate-700 text-slate-300" onClick={() => setStep(1)}>
              Back
            </Button>
            <Button type="submit" className="w-2/3 bg-blue-600 hover:bg-blue-700" disabled={isSubmittingOtp}>
              {isSubmittingOtp ? 'Verifying...' : 'Verify Code'}
            </Button>
          </div>
        </form>
      )}

      {step === 3 && (
        <form className="space-y-6" onSubmit={handleSubmitPassword(onPasswordSubmit)}>
          <p className="text-sm text-green-400 text-center mb-4">
            Email verified successfully. Enter your new password below.
          </p>
          <div>
            <Label htmlFor="password">New Password</Label>
            <div className="mt-2">
              <Input
                id="password"
                type="password"
                {...registerPassword('password')}
                className="bg-slate-950 border-slate-800"
              />
              {passwordErrors.password && (
                <p className="mt-1 text-sm text-red-400">{passwordErrors.password.message}</p>
              )}
            </div>
          </div>
          <div>
            <Label htmlFor="confirmPassword">Confirm Password</Label>
            <div className="mt-2">
              <Input
                id="confirmPassword"
                type="password"
                {...registerPassword('confirmPassword')}
                className="bg-slate-950 border-slate-800"
              />
              {passwordErrors.confirmPassword && (
                <p className="mt-1 text-sm text-red-400">{passwordErrors.confirmPassword.message}</p>
              )}
            </div>
          </div>
          <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700" disabled={isSubmittingPassword}>
            {isSubmittingPassword ? 'Resetting password...' : 'Reset Password'}
          </Button>
        </form>
      )}

      {step === 4 && (
        <div className="text-center space-y-6 mt-8">
          <p className="text-slate-300">
            Your password has been successfully reset.
          </p>
          <Link href="/login" className="inline-block w-full">
            <Button className="w-full bg-blue-600 hover:bg-blue-700">
              Sign In Now
            </Button>
          </Link>
        </div>
      )}

      {step !== 4 && (
        <p className="mt-10 text-center text-sm text-slate-400">
          Remember your password?{' '}
          <Link href="/login" className="font-semibold leading-6 text-blue-500 hover:text-blue-400">
            Back to login
          </Link>
        </p>
      )}
    </div>
  );
}
