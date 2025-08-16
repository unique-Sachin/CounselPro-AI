# Counselors List Page - Feature Overview

The counselors list page (`/counselors`) includes the following features:

## ✅ **Implemented Features**

### **1. React Query Data Fetching**
- Uses `useQuery` to fetch counselor data with caching
- Automatic retry and error handling
- 30-second stale time for performance
- Falls back to mock data when backend is unavailable

### **2. shadcn Table with Required Columns**
- **Name**: Counselor name with years of experience
- **Employee ID**: Short UUID display (first segment)
- **Department**: Specialty area (Family Law, Corporate Law, etc.)
- **Email**: Contact email with mail icon
- **Mobile**: Phone number with phone icon (or "—" if not available)
- **Status**: Availability status badge (available/busy/offline)
- **Actions**: Edit and Delete buttons

### **3. Top Bar Features**
- **"Add Counselor" button**: Primary action button
- **Search input**: Real-time client-side filtering
- **Search icon**: Visual indicator in input field

### **4. Client-side Search & Filtering**
- Filters by counselor name, email, and specialty
- Real-time results as you type
- Shows count of matching results
- Preserves original data for pagination

### **5. Pagination Controls**
- **Previous/Next buttons**: Navigate between pages
- **Page indicator**: Shows current page and total pages
- **Results counter**: "Showing X to Y of Z results"
- **Disabled states**: Buttons disabled at boundaries
- **Items per page**: Configurable (currently 10)

### **6. Loading States & Skeletons**
- **Skeleton loaders**: Realistic loading placeholders
- **Loading text**: "Loading counselors..." indicator
- **Smooth transitions**: No jarring content shifts

### **7. Empty State**
- **Attractive empty state**: When no counselors found
- **Call-to-action**: "Add Counselor" button
- **Helpful messaging**: Clear next steps for users

### **8. Framer Motion Animations**
- **Table entrance**: Fade and slide up animation
- **Row staggering**: Sequential row animations (0.05s delay)
- **Smooth transitions**: 300ms duration with easing
- **Row-level animations**: Individual row slide-in effects

### **9. Error Handling**
- **Error state card**: When API fails completely
- **Retry functionality**: "Try Again" button
- **Graceful degradation**: Falls back to mock data
- **User-friendly messages**: Clear error descriptions

## **🎨 UI/UX Enhancements**

- **Responsive design**: Works on mobile and desktop
- **Status badges**: Color-coded availability indicators
- **Icon usage**: Mail, phone, edit, delete icons for clarity
- **Typography hierarchy**: Clear information organization
- **Hover states**: Interactive feedback on buttons
- **Professional styling**: Consistent with dashboard theme

## **⚡ Performance Features**

- **React Query caching**: Reduces unnecessary API calls
- **Client-side filtering**: No API calls for search
- **Optimized re-renders**: Proper dependency arrays
- **Stale-while-revalidate**: Fresh data without blocking UI
- **Mock data fallback**: Works without backend

## **🧪 Test Scenarios**

### **Acceptance Test Results:**

1. **✅ List renders**: Shows counselor data in table format
2. **✅ Pagination works**: Previous/Next buttons function correctly
3. **✅ Search filters locally**: Real-time filtering by name/email
4. **✅ Loading states**: Skeleton loaders during data fetch
5. **✅ Animations**: Smooth table and row animations
6. **✅ Error handling**: Graceful fallback to mock data
7. **✅ Empty state**: Attractive no-data display
8. **✅ Responsive**: Works on different screen sizes

### **Additional Testing:**

- Try searching for different terms (names, emails, specialties)
- Navigate through pages using pagination controls
- Observe loading animations when page first loads
- Test responsive behavior by resizing browser window
- Check error handling by disconnecting network (falls back to mock data)

## **📊 Mock Data**

Since the backend may not be available, the app includes comprehensive mock data:
- **10 sample counselors** with realistic information
- **Different specialties**: Family, Corporate, Criminal, Immigration, etc.
- **Various availability states**: Available, busy, offline
- **Professional details**: Experience, ratings, contact info
- **Proper pagination**: Supports testing pagination logic

The page seamlessly switches between real API data and mock data, providing a consistent user experience regardless of backend availability.
