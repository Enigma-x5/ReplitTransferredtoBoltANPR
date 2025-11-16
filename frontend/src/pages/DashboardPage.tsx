import { useEffect, useState } from 'react';
import { apiClient } from '@/api/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Camera, FileText, AlertTriangle, TrendingUp } from 'lucide-react';

export default function DashboardPage() {
  const [metrics, setMetrics] = useState({
    totalCameras: 0,
    todayDetections: 0,
    pendingReviews: 0,
    activeBOLOs: 0,
  });
  const [recentEvents, setRecentEvents] = useState<any[]>([]);
  const [cameras, setCameras] = useState<any[]>([]);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      // Load cameras
      const camerasData = await apiClient.getCameras();
      setCameras(Array.isArray(camerasData) ? camerasData : []);
      
      // Load recent events
      const eventsData = await apiClient.getEvents({ limit: 5 });
      setRecentEvents(eventsData.items || []);
      
      // Load pending reviews
      const pendingData = await apiClient.getPendingEvents();
      
      // Load BOLOs
      const bolosData = await apiClient.getBOLOs();
      
      setMetrics({
        totalCameras: camerasData.length || 0,
        todayDetections: eventsData.total || 0,
        pendingReviews: pendingData.length || 0,
        activeBOLOs: bolosData.filter((b: any) => b.active).length || 0,
      });
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    }
  };

  const metricCards = [
    {
      title: 'Active Cameras',
      value: metrics.totalCameras,
      icon: Camera,
      description: 'Monitoring locations',
    },
    {
      title: "Today's Detections",
      value: metrics.todayDetections,
      icon: FileText,
      description: 'Plate reads recorded',
    },
    {
      title: 'Pending Reviews',
      value: metrics.pendingReviews,
      icon: TrendingUp,
      description: 'Awaiting verification',
    },
    {
      title: 'Active BOLOs',
      value: metrics.activeBOLOs,
      icon: AlertTriangle,
      description: 'Watch list alerts',
      accent: true,
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          System overview and recent activity
        </p>
      </div>

      {/* Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {metricCards.map((metric) => (
          <Card key={metric.title} className={metric.accent ? 'border-accent' : ''}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {metric.title}
              </CardTitle>
              <metric.icon className={`h-4 w-4 ${metric.accent ? 'text-accent' : 'text-muted-foreground'}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metric.value}</div>
              <p className="text-xs text-muted-foreground">
                {metric.description}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Map placeholder */}
      <Card>
        <CardHeader>
          <CardTitle>Camera Locations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="aspect-video bg-muted rounded-lg flex items-center justify-center">
            <p className="text-muted-foreground">
              Map view will be integrated with OlaMaps
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Recent Events */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Detections</CardTitle>
        </CardHeader>
        <CardContent>
          {recentEvents.length === 0 ? (
            <p className="text-sm text-muted-foreground">No recent events</p>
          ) : (
            <div className="space-y-2">
              {recentEvents.map((event) => (
                <div
                  key={event.id}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div>
                    <p className="font-medium">{event.plate}</p>
                    <p className="text-sm text-muted-foreground">
                      {new Date(event.captured_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">
                      {(event.confidence * 100).toFixed(1)}%
                    </p>
                    <p className="text-xs text-muted-foreground capitalize">
                      {event.review_state}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
