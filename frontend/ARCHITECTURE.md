# ANPR City Frontend Architecture

## Overview

This is a React + TypeScript single-page application (SPA) designed specifically for the ANPR City backend API. It provides a professional dashboard interface for monitoring, managing, and reviewing license plate detection events.

## Technology Stack

### Core Framework
- **React 18**: UI framework with hooks
- **TypeScript**: Type safety and better DX
- **Vite**: Fast build tool and dev server

### Routing & State
- **React Router v6**: Client-side routing
- **React Context**: Authentication state
- **React Query**: Server state management (installed, ready to use)
- **Zustand**: Additional state management (installed, ready to use)

### UI & Styling
- **Tailwind CSS**: Utility-first CSS framework
- **Shadcn/ui**: High-quality accessible components
- **Lucide React**: Icon library
- **Class Variance Authority**: Component variant management

### API Communication
- **Axios**: HTTP client with interceptors
- **OpenAPI TypeScript**: Type generation from spec (installed)

## Project Structure

```
src/
├── api/                    # API client layer
│   └── client.ts          # Centralized Axios instance + all API methods
│
├── auth/                   # Authentication module
│   ├── AuthContext.tsx    # Global auth state provider
│   ├── ProtectedRoute.tsx # Route guard component
│   └── tokenStorage.ts    # JWT storage abstraction
│
├── components/            # React components
│   ├── ui/               # Shadcn UI components (40+ components)
│   ├── AppLayout.tsx     # Main layout with sidebar
│   └── NavLink.tsx       # React Router integration
│
├── pages/                # Page-level components
│   ├── LoginPage.tsx
│   ├── DashboardPage.tsx
│   ├── CamerasPage.tsx
│   ├── UploadsPage.tsx
│   ├── EventsPage.tsx
│   ├── ReviewPage.tsx
│   ├── BOLOsPage.tsx
│   └── SystemStatusPage.tsx
│
├── hooks/                # Custom React hooks
│   ├── use-mobile.tsx
│   └── use-toast.ts
│
├── lib/                  # Utility functions
│   └── utils.ts         # cn() helper for classnames
│
├── App.tsx              # Root component with routing
├── main.tsx             # React app entry point
└── index.css            # Global styles + design system
```

## Design System

### Color Palette (HSL)

**Light Mode:**
- Background: `210 20% 98%` (Light blue-gray)
- Foreground: `217 33% 17%` (Dark navy)
- Primary: `217 91% 35%` (Professional blue)
- Accent: `43 96% 56%` (Amber for alerts)
- Success: `142 76% 36%` (Green)
- Warning: `38 92% 50%` (Orange)
- Destructive: `0 84% 60%` (Red)

**Dark Mode:**
- Background: `217 33% 10%` (Dark navy)
- Foreground: `210 20% 98%` (Light)
- Primary: `217 91% 60%` (Lighter blue)
- Accent: `43 96% 56%` (Amber)

### Design Principles
1. **Professional**: Navy/slate blue for trustworthiness
2. **Alert-focused**: Amber for BOLOs and warnings
3. **Data-dense**: Clean tables, compact layouts
4. **Accessible**: WCAG AA compliant contrast ratios
5. **Responsive**: Mobile-first with collapsible sidebar

## Authentication Flow

```
1. User visits any protected route
   ↓
2. ProtectedRoute checks auth state
   ↓
3. If no token → Redirect to /login
   ↓
4. User submits credentials
   ↓
5. POST /auth/login → Receive JWT
   ↓
6. Store token in localStorage
   ↓
7. AuthContext updates → User authenticated
   ↓
8. Redirect to /dashboard
   ↓
9. All API requests include: Authorization: Bearer <token>
   ↓
10. On 401 response → Auto logout + redirect to /login
```

### Security Considerations

**Current Implementation:**
- JWT stored in `localStorage` (centralized in one file)
- Token automatically attached to all requests
- 401 errors trigger immediate logout
- No sensitive data in token (just auth proof)

**Future Migration Path (to HttpOnly Cookies):**
- All token access is centralized in `tokenStorage.ts`
- Easy to switch to cookie-based auth without changing app code
- Just modify `tokenStorage.ts` and backend CORS settings

## API Integration

### Client Architecture

The `apiClient` in `src/api/client.ts` provides:

1. **Base Configuration**
   - Base URL from env var
   - JSON content-type by default
   - Multipart for file uploads

2. **Request Interceptor**
   - Automatically adds `Authorization: Bearer <token>` header
   - Runs on every request

3. **Response Interceptor**
   - Handles 401 errors globally
   - Clears token and redirects to login

4. **Typed Methods**
   - One method per endpoint
   - Matches OpenAPI spec exactly
   - Returns typed data

### Example API Call

```typescript
// In a component
import { apiClient } from '@/api/client';

const loadCameras = async () => {
  try {
    const cameras = await apiClient.getCameras();
    // cameras is fully typed
    setCameras(cameras);
  } catch (error) {
    // Handle error
  }
};
```

## Page Architectures

### Dashboard Page
- **Metrics Cards**: Camera count, detections, pending reviews, BOLOs
- **Map Widget**: Placeholder for OlaMaps integration
- **Recent Events**: Last 5 detections
- **Auto-refresh**: Could add polling/websockets

### Cameras Page
- **List View**: Grid of camera cards
- **Admin Actions**: Create/edit cameras
- **Clerk View**: Read-only
- **Form Validation**: Lat/lon required, heading optional

### Uploads Page
- **Upload Form**: Camera select + file input
- **Job Tracking**: Display recent jobs with status
- **Status Icons**: Visual feedback (queued/processing/done/failed)
- **File Validation**: Only video files accepted

### Events Page
- **Advanced Search**: Plate, camera, date range filters
- **Results Table**: Sortable, paginated
- **Confidence Badges**: Color-coded by score
- **Review State**: Visual status indicators

### Review Page (HITL)
- **Card Layout**: One event per card
- **Confidence Sorting**: Low confidence first (server-side)
- **Quick Actions**: Confirm or correct
- **Keyboard Shortcuts**: Ready to implement (C for confirm, E for edit)
- **Image Display**: Placeholder for crop images

### BOLOs Page
- **Alert Cards**: Highlighted active BOLOs
- **Pattern Matching**: Supports wildcards (ABC*)
- **Admin Creation**: Form with plate pattern + description
- **Active Toggle**: Enable/disable alerts

### System Status Page
- **Health Checks**: Backend status
- **License Info**: Usage metrics
- **Database Status**: Connection state
- **Storage Status**: Availability info

## State Management

### Current Approach

1. **Auth State**: React Context (`AuthContext`)
   - Global user/token state
   - Login/logout methods
   - Loading state

2. **Local State**: `useState` in components
   - Form inputs
   - UI toggles
   - Page-specific data

3. **Server State**: Direct API calls
   - No caching yet
   - Manual refetch on actions

### Future Enhancements

**React Query Integration:**
```typescript
// Example: useQuery for cameras
const { data: cameras, isLoading } = useQuery({
  queryKey: ['cameras'],
  queryFn: apiClient.getCameras,
});

// Example: useMutation for create
const createMutation = useMutation({
  mutationFn: apiClient.createCamera,
  onSuccess: () => {
    queryClient.invalidateQueries(['cameras']);
  },
});
```

Benefits:
- Automatic caching
- Background refetching
- Optimistic updates
- Loading/error states

## Routing Structure

```
/ (Index)
  → Redirects to /login or /dashboard

/login
  → Public route
  → LoginPage component

/dashboard (Protected)
  → Dashboard metrics + map
  
/cameras (Protected)
  → Camera list/management
  
/uploads (Protected)
  → Video upload + job tracking
  
/events (Protected)
  → Event search + table
  
/review (Protected)
  → HITL review queue
  
/bolos (Protected)
  → BOLO alerts management
  
/system (Protected)
  → System health + license
  
/* (404)
  → NotFound page
```

## Responsive Design

### Breakpoints (Tailwind defaults)
- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px
- `2xl`: 1400px

### Layout Behavior
- **Mobile** (<768px): Sidebar collapses, hamburger menu
- **Tablet** (768-1024px): Sidebar visible, content adapts
- **Desktop** (>1024px): Full layout with fixed sidebar

### Component Adaptations
- Tables → Responsive scroll or cards on mobile
- Forms → Stack vertically on small screens
- Cards → 1 column on mobile, 2-3 on desktop
- Sidebar → Overlay on mobile, fixed on desktop

## Performance Considerations

### Current Optimizations
- **Vite**: Fast HMR and optimized builds
- **Code Splitting**: React Router lazy loading ready
- **Tree Shaking**: Dead code elimination
- **Minification**: Production builds

### Future Optimizations
1. **Image Lazy Loading**: For event crops
2. **Virtual Scrolling**: For large event lists
3. **Debounced Search**: For event filters
4. **Service Worker**: Offline support
5. **React Query**: Caching + deduplication

## Testing Strategy (Not Yet Implemented)

### Recommended Stack
- **Vitest**: Fast unit test runner
- **React Testing Library**: Component testing
- **MSW**: API mocking
- **Playwright**: E2E testing

### Test Coverage Goals
- Auth flow (login/logout/protected routes)
- API client methods
- Form validations
- Role-based access control
- Error handling

## Deployment

### Static Hosting (Recommended)
1. Build: `npm run build`
2. Deploy `dist/` to:
   - Netlify (auto-deploy from Git)
   - Vercel (zero-config)
   - AWS S3 + CloudFront
   - Azure Static Web Apps

### Docker Deployment
```dockerfile
# Build stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Reverse Proxy Setup
If serving frontend and backend from same domain:

**Nginx Config:**
```nginx
server {
  listen 80;
  
  # Serve frontend
  location / {
    root /usr/share/nginx/html;
    try_files $uri /index.html;
  }
  
  # Proxy API to backend
  location /api {
    proxy_pass http://backend:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }
}
```

## Future Roadmap

### Short Term
- [ ] OlaMaps integration for camera locations
- [ ] Event crop image display (presigned URLs)
- [ ] Keyboard shortcuts for review queue
- [ ] Loading skeletons for better UX

### Medium Term
- [ ] Real-time event updates (WebSockets or SSE)
- [ ] Advanced filtering (multiple cameras, confidence range)
- [ ] Export functionality (CSV/JSON)
- [ ] Dark mode toggle in UI

### Long Term
- [ ] User management interface (admin)
- [ ] Analytics dashboard (charts, trends)
- [ ] Camera health monitoring
- [ ] Mobile app (React Native)
- [ ] Notifications system (browser push)

## OpenAPI Integration

### Current Status
- `openapi.yaml` copied to project root
- `openapi-typescript` package installed
- Ready to generate types

### To Generate TypeScript Types:
```bash
npx openapi-typescript openapi.yaml -o src/api/schema.ts
```

Then use in `client.ts`:
```typescript
import type { paths } from './schema';

type CameraResponse = paths['/cameras']['get']['responses']['200']['content']['application/json'];
```

### Benefits
- Type safety for API requests/responses
- Autocomplete in IDE
- Compile-time error checking
- Matches backend contract exactly

## Contributing Guidelines

### Code Style
- TypeScript strict mode
- Functional components + hooks
- Descriptive variable names
- Comments for complex logic

### Component Guidelines
- Keep components focused (single responsibility)
- Extract reusable logic to hooks
- Props interfaces at top of file
- Use semantic HTML

### API Client Guidelines
- One method per endpoint
- Return raw data (no transformation)
- Let components handle errors
- Keep client.ts organized by feature

### Design System Usage
- Use semantic color tokens (primary, accent, etc.)
- Never hardcode colors (#fff, etc.)
- Use Shadcn components when possible
- Match existing patterns

## Support & Maintenance

### Key Files to Monitor
- `src/api/client.ts` - All API integration
- `src/auth/tokenStorage.ts` - Auth persistence
- `src/index.css` - Design system
- `.env` - Configuration

### Common Maintenance Tasks
1. **Update Dependencies**: `npm update`
2. **Regenerate API Types**: When backend changes
3. **Clear localStorage**: If auth issues arise
4. **Check Console**: For runtime errors

### Debugging Tips
- Check Network tab for API failures
- Use React DevTools for component state
- Check localStorage for token presence
- Verify CORS if backend is remote
