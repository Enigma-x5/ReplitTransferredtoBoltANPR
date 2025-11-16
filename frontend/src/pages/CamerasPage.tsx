import { useEffect, useState } from 'react';
import { apiClient } from '@/api/client';
import { useAuth } from '@/auth/AuthContext';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Plus, Edit, MapPin } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface Camera {
  id: string;
  name: string;
  description?: string;
  lat: number;
  lon: number;
  heading?: number;
  rtsp_url?: string;
  active: boolean;
  created_at: string;
}

export default function CamerasPage() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingCamera, setEditingCamera] = useState<Camera | null>(null);
  const { user } = useAuth();
  const { toast } = useToast();
  const isAdmin = user?.role === 'admin';

  useEffect(() => {
    loadCameras();
  }, []);

  const loadCameras = async () => {
    try {
      const data = await apiClient.getCameras();
      setCameras(Array.isArray(data) ? data : []);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load cameras',
        variant: 'destructive',
      });
    }
  };

  const handleOpenDialog = (camera?: Camera) => {
    setEditingCamera(camera || null);
    setIsDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setIsDialogOpen(false);
    setEditingCamera(null);
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    
    const data = {
      name: formData.get('name') as string,
      description: formData.get('description') as string,
      lat: parseFloat(formData.get('lat') as string),
      lon: parseFloat(formData.get('lon') as string),
      heading: formData.get('heading') ? parseFloat(formData.get('heading') as string) : undefined,
      rtsp_url: formData.get('rtsp_url') as string || undefined,
      active: formData.get('active') === 'on',
    };

    try {
      if (editingCamera) {
        await apiClient.updateCamera(editingCamera.id, data);
        toast({ title: 'Success', description: 'Camera updated' });
      } else {
        await apiClient.createCamera(data);
        toast({ title: 'Success', description: 'Camera created' });
      }
      handleCloseDialog();
      loadCameras();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.message || 'Operation failed',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Cameras</h1>
          <p className="text-muted-foreground">
            Manage monitoring locations
          </p>
        </div>
        {isAdmin && (
          <Button onClick={() => handleOpenDialog()}>
            <Plus className="h-4 w-4 mr-2" />
            Add Camera
          </Button>
        )}
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {cameras.map((camera) => (
          <Card key={camera.id} className="border-border/50 shadow-md hover:shadow-lg transition-all hover:-translate-y-1">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${camera.active ? 'bg-success' : 'bg-muted-foreground'} animate-pulse`} />
                  <CardTitle className="text-lg">{camera.name}</CardTitle>
                </div>
                {isAdmin && (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleOpenDialog(camera)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {camera.description && (
                <p className="text-sm text-muted-foreground line-clamp-2">{camera.description}</p>
              )}
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm">
                  <MapPin className="h-4 w-4 text-primary" />
                  <span className="text-muted-foreground font-mono text-xs">
                    {camera.lat.toFixed(6)}, {camera.lon.toFixed(6)}
                  </span>
                </div>
                <div className="flex items-center justify-between pt-2 border-t border-border/50">
                  <span className="text-xs text-muted-foreground">
                    {new Date(camera.created_at).toLocaleDateString()}
                  </span>
                  {camera.active ? (
                    <Badge variant="success" className="text-xs">Active</Badge>
                  ) : (
                    <Badge variant="secondary" className="text-xs">Inactive</Badge>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Dialog open={isDialogOpen} onOpenChange={handleCloseDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <form onSubmit={handleSubmit}>
            <DialogHeader>
              <DialogTitle>
                {editingCamera ? 'Edit Camera' : 'Add Camera'}
              </DialogTitle>
              <DialogDescription>
                {editingCamera ? 'Update camera details' : 'Create a new camera location'}
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Name *</Label>
                <Input
                  id="name"
                  name="name"
                  defaultValue={editingCamera?.name}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  name="description"
                  defaultValue={editingCamera?.description}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="lat">Latitude *</Label>
                  <Input
                    id="lat"
                    name="lat"
                    type="number"
                    step="any"
                    defaultValue={editingCamera?.lat}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="lon">Longitude *</Label>
                  <Input
                    id="lon"
                    name="lon"
                    type="number"
                    step="any"
                    defaultValue={editingCamera?.lon}
                    required
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="heading">Heading (degrees)</Label>
                <Input
                  id="heading"
                  name="heading"
                  type="number"
                  step="any"
                  defaultValue={editingCamera?.heading}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="rtsp_url">RTSP URL</Label>
                <Input
                  id="rtsp_url"
                  name="rtsp_url"
                  defaultValue={editingCamera?.rtsp_url}
                />
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  id="active"
                  name="active"
                  defaultChecked={editingCamera?.active ?? true}
                />
                <Label htmlFor="active">Active</Label>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={handleCloseDialog}>
                Cancel
              </Button>
              <Button type="submit">
                {editingCamera ? 'Update' : 'Create'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
