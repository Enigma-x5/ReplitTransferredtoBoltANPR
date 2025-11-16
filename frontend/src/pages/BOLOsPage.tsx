import { useState, useEffect } from 'react';
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
import { AlertTriangle, Plus } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface BOLO {
  id: string;
  plate_pattern: string;
  description?: string;
  created_by?: string;
  active: boolean;
  created_at: string;
}

export default function BOLOsPage() {
  const [bolos, setBolos] = useState<BOLO[]>([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [platePattern, setPlatePattern] = useState('');
  const [description, setDescription] = useState('');
  const [active, setActive] = useState(true);
  const { user } = useAuth();
  const { toast } = useToast();
  const isAdmin = user?.role === 'admin';

  useEffect(() => {
    loadBOLOs();
  }, []);

  const loadBOLOs = async () => {
    try {
      const data = await apiClient.getBOLOs();
      setBolos(Array.isArray(data) ? data : []);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load BOLOs',
        variant: 'destructive',
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await apiClient.createBOLO({
        plate_pattern: platePattern,
        description,
        active,
      });

      toast({
        title: 'Success',
        description: 'BOLO created successfully',
      });

      setIsDialogOpen(false);
      setPlatePattern('');
      setDescription('');
      setActive(true);
      loadBOLOs();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.message || 'Failed to create BOLO',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">BOLOs</h1>
          <p className="text-muted-foreground">
            Be On the Lookout alerts
          </p>
        </div>
        {isAdmin && (
          <Button onClick={() => setIsDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Add BOLO
          </Button>
        )}
      </div>

      {bolos.length === 0 ? (
        <Card className="border-border/50 shadow-md">
          <CardContent className="py-16">
            <div className="text-center">
              <AlertTriangle className="mx-auto h-16 w-16 text-muted-foreground/30 mb-4" />
              <h3 className="text-xl font-semibold mb-2">No BOLOs</h3>
              <p className="text-muted-foreground">
                No alerts configured yet
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {bolos.map((bolo) => (
            <Card key={bolo.id} className={`border-border/50 shadow-md ${bolo.active ? 'border-accent/50 shadow-accent/10' : ''}`}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-xl">
                    <AlertTriangle className={`h-5 w-5 ${bolo.active ? 'text-accent' : 'text-muted-foreground'}`} />
                    <span className="font-mono">{bolo.plate_pattern}</span>
                  </CardTitle>
                  {bolo.active ? (
                    <Badge variant="warning" className="text-xs">Active</Badge>
                  ) : (
                    <Badge variant="secondary" className="text-xs">Inactive</Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {bolo.description && (
                  <p className="text-sm text-muted-foreground">
                    {bolo.description}
                  </p>
                )}
                <div className="flex items-center justify-between text-sm">
                  <span className={bolo.active ? 'text-accent font-medium' : 'text-muted-foreground'}>
                    {bolo.active ? 'Active' : 'Inactive'}
                  </span>
                  <span className="text-muted-foreground">
                    {new Date(bolo.created_at).toLocaleDateString()}
                  </span>
                </div>
                {bolo.created_by && (
                  <p className="text-xs text-muted-foreground">
                    Created by: {bolo.created_by}
                  </p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <form onSubmit={handleSubmit}>
            <DialogHeader>
              <DialogTitle>Create BOLO</DialogTitle>
              <DialogDescription>
                Add a new Be On the Lookout alert
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="plate">Plate Pattern *</Label>
                <Input
                  id="plate"
                  value={platePattern}
                  onChange={(e) => setPlatePattern(e.target.value)}
                  placeholder="ABC123 or ABC*"
                  className="font-mono"
                  required
                />
                <p className="text-xs text-muted-foreground">
                  Use * as wildcard (e.g., ABC* matches ABC123, ABCDEF)
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Reason for alert..."
                />
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="active"
                  checked={active}
                  onCheckedChange={setActive}
                />
                <Label htmlFor="active">Active</Label>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit">Create BOLO</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
