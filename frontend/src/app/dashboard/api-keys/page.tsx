'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Key, Copy, RefreshCw, AlertTriangle } from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';

export default function ApiKeysPage() {
  const [apiKey, setApiKey] = useState<string>('');
  const [isRegenerating, setIsRegenerating] = useState(false);

  useEffect(() => {
    setApiKey(localStorage.getItem('api_key') || '');
  }, []);

  const copyApiKey = () => {
    navigator.clipboard.writeText(apiKey);
    alert('API Key copied to clipboard!');
  };

  const regenerateKey = async () => {
    setIsRegenerating(true);
    try {
      const res = await api.post('/auth/rotate');
      const newKey = res.data.api_key;
      setApiKey(newKey);
      localStorage.setItem('api_key', newKey);
      alert('API Key regenerated successfully. Old key is no longer valid.');
    } catch (e) {
      console.error('Failed to regenerate key', e);
      alert('Failed to regenerate API key.');
    } finally {
      setIsRegenerating(false);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <h1 className="text-3xl font-bold tracking-tight">API Keys</h1>
      
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Key className="w-5 h-5 text-blue-500" />
            <span>Authentication Key</span>
          </CardTitle>
          <CardDescription className="text-slate-400">
            Your API key is used to authenticate the Hushh CLI client. Keep it secure and never share it publicly.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">Current API Key</label>
            <div className="flex items-center space-x-2">
              <code className="flex-1 p-3 bg-slate-950 border border-slate-800 rounded-md font-mono text-sm text-slate-300">
                {apiKey ? 'hushh_••••••••••••••••••••••••' : 'No API key found'}
              </code>
              <Button onClick={copyApiKey} variant="secondary" className="bg-slate-800 hover:bg-slate-700">
                <Copy className="w-4 h-4 mr-2" />
                Copy
              </Button>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800">
            <Dialog>
              <DialogTrigger render={<Button variant="destructive" className="bg-red-600/10 text-red-500 hover:bg-red-600/20 border border-red-500/20" />}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Regenerate Key
              </DialogTrigger>
              <DialogContent className="bg-slate-900 border-slate-800 text-slate-50">
                <DialogHeader>
                  <DialogTitle className="flex items-center text-red-500">
                    <AlertTriangle className="w-5 h-5 mr-2" />
                    Regenerate API Key?
                  </DialogTitle>
                  <DialogDescription className="text-slate-400 pt-2">
                    Are you sure you want to regenerate your API key? 
                    This action cannot be undone. Any active clients using the current key will immediately be disconnected and will need to log in again with the new key.
                  </DialogDescription>
                </DialogHeader>
                <DialogFooter className="mt-6">
                  <Button variant="outline" className="border-slate-800 bg-slate-900 text-slate-300">Cancel</Button>
                  <Button variant="destructive" onClick={regenerateKey} disabled={isRegenerating} className="bg-red-600 hover:bg-red-700 text-white">
                    {isRegenerating ? 'Regenerating...' : 'Yes, Regenerate Key'}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
