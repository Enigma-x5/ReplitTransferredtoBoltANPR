# ANPR City Frontend

Professional frontend application for the ANPR (Automatic Number Plate Recognition) city-scale monitoring system.

## Features

- **Authentication**: Secure JWT-based login with role-based access control
- **Dashboard**: Real-time metrics, camera locations map, and recent detections
- **Camera Management**: Create, view, and manage monitoring cameras (admin only)
- **Video Upload**: Upload MP4 files for processing with job tracking
- **Events Search**: Advanced filtering and search across detection events
- **Review Queue**: Human-in-the-loop verification system for detections
- **BOLO Management**: Create and manage Be On the Lookout alerts
- **System Status**: Health monitoring and license information

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** with custom design system
- **Shadcn/ui** component library
- **React Router v6** for navigation
- **Axios** for API communication
- **Zustand** for state management

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running (see backend documentation)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` and set your API base URL:
```
VITE_API_BASE_URL=http://localhost:8000/api
```

4. Start development server:
```bash
npm run dev
```

The app will be available at `http://localhost:8080`

### Building for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
src/
├── api/              # API client and request handlers
│   └── client.ts     # Axios-based API client
├── auth/             # Authentication logic
│   ├── AuthContext.tsx
│   ├── ProtectedRoute.tsx
│   └── tokenStorage.ts
├── components/       # Reusable components
│   ├── ui/          # Shadcn UI components
│   └── AppLayout.tsx # Main layout with sidebar
├── pages/           # Page components
│   ├── LoginPage.tsx
│   ├── DashboardPage.tsx
│   ├── CamerasPage.tsx
│   ├── UploadsPage.tsx
│   ├── EventsPage.tsx
│   ├── ReviewPage.tsx
│   ├── BOLOsPage.tsx
│   └── SystemStatusPage.tsx
├── hooks/           # Custom React hooks
├── lib/             # Utility functions
└── App.tsx          # Main app component
```

## API Integration

The frontend communicates with the backend API defined in `openapi.yaml`. All API calls go through the centralized `apiClient` in `src/api/client.ts`.

### Authentication

- JWT tokens are stored in `localStorage` (centralized in `tokenStorage.ts`)
- Tokens are automatically attached to all API requests via Axios interceptors
- 401 responses trigger automatic logout and redirect to login page

### Role-Based Access

- **Admin**: Full access to all features including camera management and BOLO creation
- **Clerk**: Read-only access to cameras, can upload videos and review detections

## Environment Variables

- `VITE_API_BASE_URL`: Base URL for the backend API (default: `/api`)

## Development

### Code Style

- TypeScript strict mode enabled
- ESLint for code quality
- Prettier for code formatting (recommended)

### Design System

The app uses a professional blue/slate color scheme defined in `src/index.css`:
- **Primary**: Navy blue for main actions
- **Accent**: Amber for alerts and warnings
- **Success**: Green for confirmations
- **Destructive**: Red for errors

All colors use HSL values and are theme-aware (supports dark mode).

## Security Notes

- Never commit `.env` files with real credentials
- JWT tokens are sent via `Authorization: Bearer` header only
- All user inputs should be validated server-side
- XSS protection via React's automatic escaping
- CSRF protection handled by JWT-based auth

## Future Enhancements

- [ ] Real-time WebSocket updates for events
- [ ] OlaMaps integration for camera locations
- [ ] Image crop display from backend presigned URLs
- [ ] Export functionality for labeled data
- [ ] Advanced filtering and sorting
- [ ] Keyboard shortcuts for review queue
- [ ] Dark mode toggle

## License

See backend documentation for licensing information.
