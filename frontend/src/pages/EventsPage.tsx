import { useState, useEffect } from 'react';
import { apiClient } from '@/api/client';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Search, Calendar } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface Event {
  id: string;
  plate: string;
  normalized_plate: string;
  confidence: number;
  camera_id: string;
  captured_at: string;
  review_state: string;
}

export default function EventsPage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [cameras, setCameras] = useState<any[]>([]);
  const [filters, setFilters] = useState({
    plate: '',
    camera_id: '',
    from_ts: '',
    to_ts: '',
  });
  const { toast } = useToast();

  useEffect(() => {
    loadCameras();
    loadEvents();
  }, []);

  const loadCameras = async () => {
    try {
      const data = await apiClient.getCameras();
      setCameras(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to load cameras:', error);
    }
  };

  const loadEvents = async () => {
    try {
      const params: any = {};
      if (filters.plate) params.plate = filters.plate;
      if (filters.camera_id) params.camera_id = filters.camera_id;
      if (filters.from_ts) params.from_ts = filters.from_ts;
      if (filters.to_ts) params.to_ts = filters.to_ts;

      const data = await apiClient.getEvents(params);
      setEvents(data.items || []);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load events',
        variant: 'destructive',
      });
    }
  };

  const handleSearch = () => {
    loadEvents();
  };

  const getCameraName = (cameraId: string) => {
    const camera = cameras.find((c) => c.id === cameraId);
    return camera?.name || cameraId;
  };

  const getConfidenceBadge = (confidence: number) => {
    const percentage = confidence * 100;
    let colorClass = 'bg-success/10 text-success';
    if (percentage < 70) colorClass = 'bg-destructive/10 text-destructive';
    else if (percentage < 85) colorClass = 'bg-warning/10 text-warning';
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${colorClass}`}>
        {percentage.toFixed(1)}%
      </span>
    );
  };

  const getReviewStateBadge = (state: string) => {
    const colors: Record<string, string> = {
      unreviewed: 'bg-muted text-muted-foreground',
      confirmed: 'bg-success/10 text-success',
      corrected: 'bg-primary/10 text-primary',
      rejected: 'bg-destructive/10 text-destructive',
    };
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium capitalize ${colors[state] || colors.unreviewed}`}>
        {state}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Events</h1>
        <p className="text-muted-foreground">
          Search and view detection events
        </p>
      </div>

      {/* Search Filters */}
      <Card className="border-border/50 shadow-md">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Search className="h-5 w-5 text-primary" />
            Search Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-2">
              <Label htmlFor="plate">Plate Number</Label>
              <Input
                id="plate"
                placeholder="ABC123"
                value={filters.plate}
                onChange={(e) => setFilters({ ...filters, plate: e.target.value })}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="camera">Camera</Label>
              <Select
                value={filters.camera_id}
                onValueChange={(value) => setFilters({ ...filters, camera_id: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All cameras" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All cameras</SelectItem>
                  {cameras.map((camera) => (
                    <SelectItem key={camera.id} value={camera.id}>
                      {camera.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="from">From Date</Label>
              <Input
                id="from"
                type="datetime-local"
                value={filters.from_ts}
                onChange={(e) => setFilters({ ...filters, from_ts: e.target.value })}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="to">To Date</Label>
              <Input
                id="to"
                type="datetime-local"
                value={filters.to_ts}
                onChange={(e) => setFilters({ ...filters, to_ts: e.target.value })}
              />
            </div>
          </div>
          
          <div className="mt-4">
            <Button onClick={handleSearch}>
              <Search className="mr-2 h-4 w-4" />
              Search
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results Table */}
      <Card>
        <CardHeader>
          <CardTitle>Results ({events.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Plate</TableHead>
                  <TableHead>Normalized</TableHead>
                  <TableHead>Confidence</TableHead>
                  <TableHead>Camera</TableHead>
                  <TableHead>Captured At</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {events.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center text-muted-foreground">
                      No events found
                    </TableCell>
                  </TableRow>
                ) : (
                  events.map((event) => (
                    <TableRow key={event.id}>
                      <TableCell className="font-mono font-medium">
                        {event.plate}
                      </TableCell>
                      <TableCell className="font-mono text-muted-foreground">
                        {event.normalized_plate}
                      </TableCell>
                      <TableCell>{getConfidenceBadge(event.confidence)}</TableCell>
                      <TableCell>{getCameraName(event.camera_id)}</TableCell>
                      <TableCell>
                        {new Date(event.captured_at).toLocaleString()}
                      </TableCell>
                      <TableCell>{getReviewStateBadge(event.review_state)}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
