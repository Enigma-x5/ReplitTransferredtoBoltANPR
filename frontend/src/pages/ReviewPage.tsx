import { useState, useEffect } from 'react';
import { apiClient } from '@/api/client';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { CheckCircle, Edit3, AlertCircle } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface PendingEvent {
  id: string;
  plate: string;
  normalized_plate: string;
  confidence: number;
  camera_id: string;
  captured_at: string;
  crop_path?: string;
}

export default function ReviewPage() {
  const [pendingEvents, setPendingEvents] = useState<PendingEvent[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<PendingEvent | null>(null);
  const [isCorrectDialogOpen, setIsCorrectDialogOpen] = useState(false);
  const [correctedPlate, setCorrectedPlate] = useState('');
  const [comments, setComments] = useState('');
  const { toast } = useToast();

  useEffect(() => {
    loadPendingEvents();
  }, []);

  const loadPendingEvents = async () => {
    try {
      const data = await apiClient.getPendingEvents();
      setPendingEvents(Array.isArray(data) ? data : []);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load pending events',
        variant: 'destructive',
      });
    }
  };

  const handleConfirm = async (event: PendingEvent) => {
    try {
      await apiClient.confirmEvent(event.id, {
        notes: 'Confirmed by reviewer',
      });
      
      toast({
        title: 'Confirmed',
        description: 'Detection confirmed successfully',
      });
      
      setPendingEvents(prev => prev.filter(e => e.id !== event.id));
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.message || 'Failed to confirm',
        variant: 'destructive',
      });
    }
  };

  const handleOpenCorrect = (event: PendingEvent) => {
    setSelectedEvent(event);
    setCorrectedPlate(event.plate);
    setComments('');
    setIsCorrectDialogOpen(true);
  };

  const handleSubmitCorrection = async () => {
    if (!selectedEvent) return;

    try {
      await apiClient.correctEvent(selectedEvent.id, {
        corrected_plate: correctedPlate,
        comments,
      });
      
      toast({
        title: 'Corrected',
        description: 'Correction submitted successfully',
      });
      
      setPendingEvents(prev => prev.filter(e => e.id !== selectedEvent.id));
      setIsCorrectDialogOpen(false);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.message || 'Failed to submit correction',
        variant: 'destructive',
      });
    }
  };

  const getConfidenceBadge = (confidence: number) => {
    const percentage = confidence * 100;
    if (percentage >= 85) return 'High';
    if (percentage >= 70) return 'Medium';
    return 'Low';
  };

  const getConfidenceColor = (confidence: number) => {
    const percentage = confidence * 100;
    if (percentage >= 85) return 'text-success';
    if (percentage >= 70) return 'text-warning';
    return 'text-destructive';
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Review Queue</h1>
        <p className="text-muted-foreground">
          Human-in-the-loop verification ({pendingEvents.length} pending)
        </p>
      </div>

      {pendingEvents.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <CheckCircle className="mx-auto h-12 w-12 text-success mb-4" />
              <h3 className="text-lg font-semibold mb-2">All caught up!</h3>
              <p className="text-muted-foreground">
                No pending reviews at the moment
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {pendingEvents.map((event) => (
            <Card key={event.id} className="overflow-hidden">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center justify-between">
                  <span className="font-mono text-lg">{event.plate}</span>
                  <span className={`text-sm ${getConfidenceColor(event.confidence)}`}>
                    {getConfidenceBadge(event.confidence)} ({(event.confidence * 100).toFixed(1)}%)
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Image placeholder */}
                <div className="aspect-video bg-muted rounded-lg flex items-center justify-center">
                  <p className="text-sm text-muted-foreground">
                    {event.crop_path ? 'Image crop available' : 'No crop image'}
                  </p>
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Normalized:</span>
                    <span className="font-mono">{event.normalized_plate}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Captured:</span>
                    <span>{new Date(event.captured_at).toLocaleString()}</span>
                  </div>
                </div>

                <div className="flex gap-2 pt-2">
                  <Button
                    variant="default"
                    size="sm"
                    className="flex-1"
                    onClick={() => handleConfirm(event)}
                  >
                    <CheckCircle className="h-4 w-4 mr-1" />
                    Confirm
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={() => handleOpenCorrect(event)}
                  >
                    <Edit3 className="h-4 w-4 mr-1" />
                    Correct
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Correction Dialog */}
      <Dialog open={isCorrectDialogOpen} onOpenChange={setIsCorrectDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Correct Detection</DialogTitle>
            <DialogDescription>
              Submit the correct plate number for this detection
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {selectedEvent && (
              <div className="p-3 bg-muted rounded-lg">
                <p className="text-sm text-muted-foreground">Original:</p>
                <p className="font-mono text-lg font-bold">{selectedEvent.plate}</p>
              </div>
            )}
            
            <div className="space-y-2">
              <Label htmlFor="corrected">Corrected Plate *</Label>
              <Input
                id="corrected"
                value={correctedPlate}
                onChange={(e) => setCorrectedPlate(e.target.value)}
                placeholder="Enter correct plate"
                className="font-mono"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="comments">Comments</Label>
              <Textarea
                id="comments"
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                placeholder="Optional notes about the correction"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCorrectDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmitCorrection} disabled={!correctedPlate}>
              Submit Correction
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
