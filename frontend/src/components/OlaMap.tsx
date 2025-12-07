import { useEffect, useRef, useState } from 'react';
import { apiClient } from '@/api/client';

interface Camera {
  id: string;
  name: string;
  lat: number;
  lon: number;
  active?: boolean;
}

interface OlaMapProps {
  cameras: Camera[];
  height?: string;
}

declare global {
  interface Window {
    OlaMaps: any;
  }
}

export default function OlaMap({ cameras, height = '400px' }: OlaMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scriptLoaded, setScriptLoaded] = useState(false);

  useEffect(() => {
    if (document.querySelector('script[src*="olamaps-web-sdk"]')) {
      setScriptLoaded(true);
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://www.unpkg.com/olamaps-web-sdk@latest/dist/olamaps-web-sdk.umd.js';
    script.async = true;
    script.onload = () => setScriptLoaded(true);
    script.onerror = () => setError('Failed to load Ola Maps SDK');
    document.head.appendChild(script);

    return () => {
    };
  }, []);

  useEffect(() => {
    if (!scriptLoaded || !mapContainerRef.current) return;

    let timeoutId: NodeJS.Timeout;
    let isMapLoaded = false;

    const initMap = async () => {
      try {
        const config = await apiClient.getMapConfig();
        
        if (!config.api_key) {
          setError('Ola Maps API key not configured');
          setLoading(false);
          return;
        }

        if (!window.OlaMaps) {
          setError('Ola Maps SDK not loaded');
          setLoading(false);
          return;
        }

        const olaMaps = new window.OlaMaps({
          apiKey: config.api_key
        });

        const defaultCenter = cameras.length > 0 
          ? [cameras[0].lon, cameras[0].lat] 
          : [77.5946, 12.9716];

        const map = olaMaps.init({
          style: config.style_url,
          container: mapContainerRef.current,
          center: defaultCenter,
          zoom: 12
        });

        mapInstanceRef.current = map;

        const addMarkers = () => {
          if (isMapLoaded) return;
          isMapLoaded = true;
          
          cameras.forEach((camera) => {
            if (camera.lat && camera.lon) {
              try {
                const popup = olaMaps.addPopup({
                  offset: [0, -30],
                  anchor: 'bottom'
                }).setHTML(`
                  <div style="padding: 8px;">
                    <strong>${camera.name}</strong>
                    <p style="margin: 4px 0 0 0; font-size: 12px; color: ${camera.active ? '#22c55e' : '#ef4444'};">
                      ${camera.active ? 'Active' : 'Inactive'}
                    </p>
                  </div>
                `);

                const marker = olaMaps.addMarker({
                  offset: [0, 6],
                  anchor: 'bottom',
                  color: camera.active ? '#22c55e' : '#ef4444'
                })
                  .setLngLat([camera.lon, camera.lat])
                  .setPopup(popup)
                  .addTo(map);
                
                markersRef.current.push(marker);
              } catch (markerErr) {
                console.warn('Failed to add marker for camera:', camera.name, markerErr);
              }
            }
          });

          if (cameras.length > 1) {
            try {
              const bounds: [number, number, number, number] = [
                Math.min(...cameras.map(c => c.lon)),
                Math.min(...cameras.map(c => c.lat)),
                Math.max(...cameras.map(c => c.lon)),
                Math.max(...cameras.map(c => c.lat))
              ];
              
              map.fitBounds(bounds, { padding: 50 });
            } catch (boundsErr) {
              console.warn('Failed to fit bounds:', boundsErr);
            }
          }

          setLoading(false);
        };

        map.on('load', addMarkers);

        timeoutId = setTimeout(() => {
          if (!isMapLoaded) {
            console.log('Map load timeout, adding markers anyway');
            addMarkers();
          }
        }, 5000);

        map.on('error', (e: any) => {
          console.warn('Map warning:', e);
        });

      } catch (err: any) {
        console.error('Failed to initialize map:', err);
        setError(err?.message || 'Failed to initialize map. Please check your API key.');
        setLoading(false);
      }
    };

    initMap();

    return () => {
      if (timeoutId) clearTimeout(timeoutId);
      markersRef.current.forEach(marker => {
        if (marker && marker.remove) {
          marker.remove();
        }
      });
      markersRef.current = [];
      
      if (mapInstanceRef.current && mapInstanceRef.current.remove) {
        mapInstanceRef.current.remove();
      }
    };
  }, [scriptLoaded, cameras]);

  if (error) {
    return (
      <div 
        className="bg-muted rounded-lg flex items-center justify-center"
        style={{ height }}
      >
        <p className="text-destructive">{error}</p>
      </div>
    );
  }

  return (
    <div className="relative rounded-lg overflow-hidden" style={{ height }}>
      {loading && (
        <div className="absolute inset-0 bg-muted flex items-center justify-center z-10">
          <div className="flex flex-col items-center gap-2">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <p className="text-sm text-muted-foreground">Loading map...</p>
          </div>
        </div>
      )}
      <div 
        ref={mapContainerRef} 
        className="w-full h-full"
        style={{ height }}
      />
    </div>
  );
}
