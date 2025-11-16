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
import { Upload, CheckCircle, Clock, XCircle, Loader2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface UploadJob {
  job_id: string;
  status: 'queued' | 'processing' | 'done' | 'failed';
  created_at: string;
}

export default function UploadsPage() {
  const [cameras, setCameras] = useState<any[]>([]);
  const [selectedCamera, setSelectedCamera] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [jobs, setJobs] = useState<UploadJob[]>([]);
  const { toast } = useToast();

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

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (!selectedFile.type.startsWith('video/')) {
        toast({
          title: 'Invalid file',
          description: 'Please select a video file',
          variant: 'destructive',
        });
        return;
      }
      setFile(selectedFile);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedCamera || !file) {
      toast({
        title: 'Missing information',
        description: 'Please select a camera and video file',
        variant: 'destructive',
      });
      return;
    }

    setIsUploading(true);
    
    try {
      const result = await apiClient.uploadVideo(selectedCamera, file);
      toast({
        title: 'Upload started',
        description: `Job ID: ${result.job_id}`,
      });
      
      // Add to jobs list
      setJobs(prev => [result, ...prev]);
      
      // Reset form
      setFile(null);
      setSelectedCamera('');
      const fileInput = document.getElementById('file') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
    } catch (error: any) {
      toast({
        title: 'Upload failed',
        description: error.response?.data?.message || 'Failed to upload video',
        variant: 'destructive',
      });
    } finally {
      setIsUploading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'done':
        return <CheckCircle className="h-5 w-5 text-success" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-destructive" />;
      case 'processing':
        return <Loader2 className="h-5 w-5 text-primary animate-spin" />;
      default:
        return <Clock className="h-5 w-5 text-muted-foreground" />;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Upload Video</h1>
        <p className="text-muted-foreground">
          Upload MP4 files for processing
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Upload Form */}
        <Card className="border-border/50 shadow-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5 text-primary" />
              New Upload
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="camera">Camera *</Label>
                <Select value={selectedCamera} onValueChange={setSelectedCamera}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select camera" />
                  </SelectTrigger>
                  <SelectContent>
                    {cameras.map((camera) => (
                      <SelectItem key={camera.id} value={camera.id}>
                        {camera.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="file">Video File *</Label>
                <Input
                  id="file"
                  type="file"
                  accept="video/mp4,video/*"
                  onChange={handleFileChange}
                  disabled={isUploading}
                />
                {file && (
                  <p className="text-sm text-muted-foreground">
                    Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                  </p>
                )}
              </div>

              <Button type="submit" className="w-full" disabled={isUploading}>
                {isUploading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Upload Video
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Jobs Status */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Jobs</CardTitle>
          </CardHeader>
          <CardContent>
            {jobs.length === 0 ? (
              <p className="text-sm text-muted-foreground">No jobs yet</p>
            ) : (
              <div className="space-y-3">
                {jobs.map((job) => (
                  <div
                    key={job.job_id}
                    className="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      {getStatusIcon(job.status)}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-mono truncate">{job.job_id}</p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(job.created_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <span className="text-sm font-medium capitalize">
                      {job.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
