import { useEffect, useState } from 'react';
import { apiClient } from '@/api/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Server, Database, Activity, HardDrive } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

export default function SystemStatusPage() {
  const [health, setHealth] = useState<any>(null);
  const [usage, setUsage] = useState<any>(null);
  const { toast } = useToast();

  useEffect(() => {
    loadSystemInfo();
  }, []);

  const loadSystemInfo = async () => {
    try {
      const [healthData, usageData] = await Promise.all([
        apiClient.getHealth(),
        apiClient.getLicenseUsage().catch(() => null),
      ]);
      
      setHealth(healthData);
      setUsage(usageData);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load system information',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">System Status</h1>
        <p className="text-muted-foreground">
          Health checks and license information
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* System Health */}
        <Card className="border-border/50 shadow-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Activity className="h-5 w-5 text-primary" />
              System Health
            </CardTitle>
          </CardHeader>
          <CardContent>
            {health ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Status</span>
                  <Badge variant={health.status === 'healthy' ? 'default' : 'destructive'}>
                    {health.status || 'Unknown'}
                  </Badge>
                </div>
                {health.timestamp && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Last Check</span>
                    <span className="text-sm">
                      {new Date(health.timestamp).toLocaleString()}
                    </span>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Loading...</p>
            )}
          </CardContent>
        </Card>

        {/* License Usage */}
        <Card className="border-border/50 shadow-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Server className="h-5 w-5 text-primary" />
              License Usage
            </CardTitle>
          </CardHeader>
          <CardContent>
            {usage ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Camera Count</span>
                  <span className="text-sm font-medium">{usage.camera_count || 0}</span>
                </div>
                {usage.last_report_at && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Last Report</span>
                    <span className="text-sm">
                      {new Date(usage.last_report_at).toLocaleString()}
                    </span>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No usage data available</p>
            )}
          </CardContent>
        </Card>

        {/* Database Info */}
        <Card className="border-border/50 shadow-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Database className="h-5 w-5 text-primary" />
              Database
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Connection</span>
                <Badge variant="default">Active</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Type</span>
                <span className="text-sm">PostgreSQL</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Storage Info */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <HardDrive className="h-5 w-5" />
              Storage
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Status</span>
                <Badge variant="default">Available</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Type</span>
                <span className="text-sm">Cloud Storage</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
