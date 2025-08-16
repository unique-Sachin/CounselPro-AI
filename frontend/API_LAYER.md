# CounselPro AI Frontend API Layer

This document describes the typed API layer implementation for the CounselPro AI frontend application.

## Architecture Overview

The API layer consists of:
- **Types**: TypeScript interfaces matching the OpenAPI specification
- **API Client**: Axios-based HTTP client with interceptors
- **Service Functions**: Organized business logic for API calls
- **Error Handling**: Automatic toast notifications for common errors

## File Structure

```
src/lib/
├── types.ts           # TypeScript interfaces for API models
├── api.ts            # Axios client and helper functions
├── services/
│   ├── counselors.ts # Counselor-related API functions
│   ├── sessions.ts   # Session-related API functions
│   └── index.ts      # Service exports
└── api-examples.ts   # Usage examples
```

## Types (`src/lib/types.ts`)

### Counselor Types
- `CounselorResponse`: Full counselor data from API
- `CounselorCreate`: Data required to create a counselor
- `CounselorUpdate`: Optional fields for updating a counselor

### Session Types
- `SessionResponse`: Full session data from API
- `SessionCreate`: Data required to create a session
- `SessionUpdate`: Optional fields for updating a session

### Utility Types
- `PaginatedResponse<T>`: Wrapper for paginated API responses
- `ApiError`: Error response structure
- `PaginationParams`: Query parameters for pagination

## API Client (`src/lib/api.ts`)

### Base Configuration
- **Base URL**: `process.env.NEXT_PUBLIC_API_BASE_URL` (defaults to `http://localhost:8000`)
- **Timeout**: 10 seconds
- **Content-Type**: `application/json`

### Error Handling
- **401 Unauthorized**: Shows toast notification
- **422 Validation**: Shows detailed error message with special handling for session ID format issues
- **500+ Server Errors**: Shows generic server error message

### Helper Functions
- `apiHelpers.get<T>(url, params)`: GET requests
- `apiHelpers.post<T>(url, data)`: POST requests
- `apiHelpers.put<T>(url, data)`: PUT requests
- `apiHelpers.del<T>(url, params)`: DELETE requests

## Service Functions

### Counselor Service (`src/lib/services/counselors.ts`)

```typescript
// List counselors with pagination
await listCounselors({ skip: 0, limit: 10 })
// → GET /counselors?skip=0&limit=10

// Create a new counselor
await createCounselor(counselorData)
// → POST /counselors

// Get counselor by UID (accepts string)
await getCounselor("counselor-uid-123")
// → GET /counselors/counselor-uid-123

// Update counselor by UID
await updateCounselor("counselor-uid-123", updates)
// → PUT /counselors/counselor-uid-123

// Delete counselor by UID
await deleteCounselor("counselor-uid-123")
// → DELETE /counselors/counselor-uid-123?counselor_uid=counselor-uid-123
```

### Session Service (`src/lib/services/sessions.ts`)

```typescript
// Create a new session
await createSession(sessionData)
// → POST /sessions

// Get session by ID or UID (accepts string)
await getSession("session-id-or-uid")
// → GET /sessions/session-id-or-uid

// Update session by ID or UID
await updateSession("session-id-or-uid", updates)
// → PUT /sessions/session-id-or-uid

// Delete session by ID or UID
await deleteSession("session-id-or-uid")
// → DELETE /sessions/session-id-or-uid

// List sessions by counselor ID
await listSessionsByCounselor(1, { skip: 0, limit: 10 })
// → GET /sessions/by-counselor/1?skip=0&limit=10
```

## Usage Examples

### Basic Usage

```typescript
import { listCounselors, createCounselor } from '@/lib/services/counselors';
import { CounselorCreate } from '@/lib/types';

// List counselors
const counselors = await listCounselors({ skip: 0, limit: 5 });

// Create counselor
const newCounselor: CounselorCreate = {
  name: "Dr. Jane Smith",
  specialty: "Family Law",
  email: "jane.smith@counselpro.ai",
  availability_status: "available"
};
const created = await createCounselor(newCounselor);
```

### With React Query (Recommended)

```typescript
import { useQuery, useMutation } from '@tanstack/react-query';
import { listCounselors, createCounselor } from '@/lib/services/counselors';

function CounselorList() {
  // Query for data
  const { data: counselors, isLoading } = useQuery({
    queryKey: ['counselors', { skip: 0, limit: 10 }],
    queryFn: () => listCounselors({ skip: 0, limit: 10 })
  });

  // Mutation for creating
  const createMutation = useMutation({
    mutationFn: createCounselor,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['counselors'] });
    }
  });

  // Component JSX...
}
```

## Error Handling

The API layer automatically handles common error scenarios:

- **Network errors**: Axios will throw and can be caught
- **422 Validation errors**: Toast notification with details
- **401 Unauthorized**: Toast notification about auth issues
- **Session ID format issues**: Special handling with backend alignment suggestion
- **500+ Server errors**: Generic error toast

## Testing

Use the API Test page at `/api-test` to:
1. Test all API endpoints
2. Verify correct URLs are being called
3. Check request/response handling
4. Validate error scenarios

## Environment Variables

Required environment variables:

```env
# .env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Notes

- Session endpoints accept both integer IDs and string UIDs, but the backend may expect specific formats
- The API client includes 422 error handling for session ID format mismatches
- All service functions return typed responses based on the OpenAPI specification
- Pagination parameters default to `{ skip: 0, limit: 10 }` if not provided
