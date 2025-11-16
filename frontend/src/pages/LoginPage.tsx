import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Shield, AlertCircle, Copy } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.message || 'Invalid credentials. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: 'Copied',
      description: 'Credential copied to clipboard',
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md space-y-6">
        {/* Main Login Card */}
        <Card className="shadow-xl border-border/50">
          <CardHeader className="space-y-4 flex flex-col items-center text-center pb-8 pt-10">
            <div className="flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 ring-4 ring-primary/20">
              <Shield className="h-8 w-8 text-primary" />
            </div>
            <div className="space-y-2">
              <h1 className="font-bold text-3xl">ANPR System</h1>
              <CardTitle className="text-2xl font-semibold">Sign In</CardTitle>
              <CardDescription className="text-base">
                Enter your credentials to access the system
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent className="pb-8">
            <form onSubmit={handleSubmit} className="space-y-5">
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
              
              <div className="space-y-2">
                <Label htmlFor="email" className="text-sm font-medium">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  className="h-11"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="password" className="text-sm font-medium">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  className="h-11"
                />
              </div>

              <Button 
                type="submit" 
                className="w-full h-11 text-base font-semibold"
                disabled={isLoading}
              >
                {isLoading ? 'Signing in...' : 'Sign In'}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Demo Credentials Card */}
        <Card className="shadow-lg border-accent/30 bg-card/80 backdrop-blur">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <Shield className="h-4 w-4 text-accent" />
              Demo Credentials
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <div className="flex items-center justify-between p-3 rounded-lg bg-background/50 border border-border/50">
                <div className="space-y-0.5">
                  <p className="text-xs text-muted-foreground font-medium">Admin Account</p>
                  <p className="text-sm font-mono">admin@example.com</p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => copyToClipboard('admin@example.com')}
                  type="button"
                >
                  <Copy className="h-3.5 w-3.5" />
                </Button>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-background/50 border border-border/50">
                <div className="space-y-0.5">
                  <p className="text-xs text-muted-foreground font-medium">Operator Account</p>
                  <p className="text-sm font-mono">clerk@example.com / clerk</p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => copyToClipboard('clerk@example.com')}
                  type="button"
                >
                  <Copy className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
            <p className="text-xs text-muted-foreground text-center pt-1">
              Click to copy credentials for quick testing
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
