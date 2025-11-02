# Hebrew Meeting Summarizer - Frontend Specification
## Firebase Studio Prototyper / Frontend Development Prompt

### Project Overview

Build a state-of-the-art B2B-SaaS web application for Hebrew meeting summarization with speaker-aware transcription. The application should have a modern, clean, professional aesthetic inspired by leading Israeli tech companies (Wix, Fiverr, Monday.com, Check Point) - combining minimalist design with powerful functionality.

### Design Philosophy: Israeli SOTA B2B-SaaS

**Visual Characteristics:**
- **Color Palette**: 
  - Primary: Deep blue (#1E3A8A) or teal (#14B8A6) - professional, trustworthy
  - Secondary: Purple accent (#7C3AED) or orange (#F59E0B) - innovative, energetic
  - Background: Clean whites (#FFFFFF) with subtle grays (#F9FAFB, #F3F4F6)
  - Text: Dark gray (#111827, #1F2937) for body, pure black (#000000) for headings
  - Success: Green (#10B981), Warning: Amber (#F59E0B), Error: Red (#EF4444)
  - Hebrew text support with RTL layouts

- **Typography**:
  - Primary font: Inter, SF Pro, or similar modern sans-serif (Hebrew: Alef, Assistant, Varela Round)
  - Headings: Bold, 24px-48px, strong hierarchy
  - Body: 16px base, 14px for secondary text
  - Line height: 1.6 for readability
  - Support for Hebrew/Arabic RTL text with proper directionality

- **Spacing & Layout**:
  - Generous whitespace (24px, 32px, 48px grid)
  - Card-based layouts with subtle shadows (0 1px 3px rgba(0,0,0,0.1))
  - Rounded corners: 8px-12px for cards, 6px for buttons
  - Consistent padding: 16px, 24px, 32px

- **UI Elements**:
  - Flat design with subtle depth
  - Smooth animations (200-300ms transitions)
  - Hover states: subtle scale (1.02) or color shifts
  - Loading states: Skeleton loaders, progress indicators
  - Empty states: Illustrations with helpful messaging

### Technology Stack

**Framework:**
- Next.js 14+ (App Router)
- TypeScript (strict mode)
- React 18+ with hooks
- Tailwind CSS for styling

**State Management:**
- Zustand for global state (meetings, speakers, user)
- React Query for server state and caching
- Local component state for UI interactions

**UI Libraries:**
- Shadcn/ui or Radix UI for accessible components
- Framer Motion for animations
- React Hook Form + Zod for forms
- React Audio Player or Wavesurfer.js for audio playback

**Additional:**
- Socket.io-client for WebSocket real-time updates
- RecordRTC or MediaRecorder API for audio capture
- Axios or Fetch for API calls
- date-fns for date formatting
- i18next for internationalization (Hebrew/English)

### Application Structure

#### 1. Authentication & Onboarding

**Login Page** (`/login`)
- Clean, centered login form
- Email/password or SSO (Auth0/Google/Microsoft)
- Hebrew and English language toggle
- "Remember me" checkbox
- Forgot password link
- Branded logo and tagline

**Sign Up / Onboarding** (`/signup`, `/onboarding`)
- Multi-step onboarding wizard
- Organization creation
- Welcome tour/interactive tutorial
- Initial preferences setup

**Dashboard Layout**
- Left sidebar navigation (collapsible)
- Top header with user menu, notifications, search
- Main content area with breadcrumbs
- Footer with links and company info

#### 2. Dashboard - Meeting List (`/dashboard`)

**Main View:**
- Grid/list toggle view
- Filter bar: Date range, status (pending/processing/completed), tags
- Search bar: Search by title, participant names, keywords
- Sort options: Date (newest/oldest), Duration, Status
- Bulk actions: Export, delete, archive

**Meeting Cards:**
- Thumbnail/preview (if available)
- Title with status badge
- Date & duration
- Number of speakers detected
- Completion status indicator
- Quick actions: View, Edit, Delete
- Hover effect: Show preview/quick stats

**Empty State:**
- Illustration showing empty dashboard
- CTA: "Upload Your First Meeting"
- Helpful tips or getting started guide

**Stats Widget:**
- Total meetings processed
- Total minutes transcribed
- Active speakers identified
- Processing accuracy metrics

#### 3. Meeting Upload/Recording (`/meetings/new`)

**Upload Tab:**
- Drag-and-drop zone (with visual feedback)
- File browser button
- Supported formats: MP3, WAV, M4A, AAC, WebM
- File size limit indicator
- Preview selected file (duration, size, waveform)
- Title input field
- Optional: Add tags, description, scheduled date
- Submit button with loading state

**Live Recording Tab:**
- Large "Start Recording" button
- Microphone permission request handling
- Real-time audio level indicator (waveform/bar)
- Recording timer (MM:SS)
- Pause/Resume controls
- Stop and save button
- Audio preview before submission
- Browser compatibility warnings

**Processing Status:**
- Progress indicator with steps:
  1. Uploading...
  2. Transcribing...
  3. Identifying speakers...
  4. Generating summary...
  5. Complete ✓
- Estimated time remaining
- Cancel option (if applicable)

#### 4. Meeting Detail View (`/meetings/[id]`)

**Header Section:**
- Meeting title (editable)
- Status badge (Processing/Completed/Failed)
- Date and duration
- Action buttons: Share, Export, Delete, Settings

**Tab Navigation:**
- Overview
- Transcript
- Speakers
- Summary
- Analytics

**Overview Tab:**
- Key metrics cards:
  - Duration, Speaker count, Word count
  - Confidence score, Processing time
- Quick summary preview (first paragraph)
- Key points bullet list
- Action items highlight
- Timeline visualization

**Transcript Tab:**
- Scrollable transcript viewer
- Speaker-labeled segments with color coding
- Timestamp navigation (click to jump)
- Search within transcript (highlight matches)
- Copy segments button
- Export options: TXT, JSON, SRT
- Play audio with transcript sync (highlight current segment)
- Filter by speaker
- Expandable/collapsible segments

**Speakers Tab:**
- Grid/list of detected speakers
- Each speaker card shows:
  - 15-second audio snippet player (play/pause)
  - Speaker label (SPK_1, SPK_2, etc.)
  - Name input field (with suggestions dropdown)
  - Name suggestions with confidence scores
  - "Assign Name" button
  - Voiceprint similarity match (if found)
  - Total speaking time
  - Number of segments

**Speaker Assignment Modal:**
- Large audio player for snippet
- Name input with autocomplete (suggested names from transcript)
- Confidence indicator
- "This is a new speaker" checkbox
- Cancel/Save buttons
- Success animation on assignment

**Summary Tab:**
- Markdown-formatted summary
- Speaker-aware sections (if applicable)
- Key points expandable list
- Action items with checkboxes (if extracted)
- Topics/categories tags
- Sentiment indicators (if available)
- Export: PDF, DOCX, Markdown

**Analytics Tab:**
- Charts and visualizations:
  - Speaking time distribution (pie chart)
  - Timeline heatmap (who spoke when)
  - Word frequency analysis
  - Sentiment over time
  - Topics/entities extraction
- Interactive charts (zoom, filter)

#### 5. Speaker Management (`/speakers`)

**Speaker List View:**
- Grid of speaker profiles
- Each card shows:
  - Avatar (initials or uploaded photo)
  - Name
  - Organization/tags
  - Number of meetings participated
  - Last seen date
  - Voiceprint confidence
- Search and filter by name, organization
- Sort by name, activity, creation date

**Speaker Detail View** (`/speakers/[id]`):
- Profile header
- Stats: Total meetings, Total speaking time
- Associated meetings list
- Voiceprint details (technical, optional)
- Edit/Delete actions

#### 6. Settings (`/settings`)

**Organization Settings:**
- Organization name and details
- Subscription plan and billing
- Member management (invite, roles, permissions)
- API keys and integrations

**User Preferences:**
- Profile information
- Language preference (Hebrew/English)
- Notification settings
- Audio playback preferences
- Export defaults

**Advanced Settings:**
- Transcription quality settings
- Speaker recognition sensitivity
- Name extraction preferences
- Summary template customization

#### 7. Real-time Meeting View (`/meetings/[id]/live`)

**Live Transcription Display:**
- Real-time scrolling transcript
- Speaker labels appear as they speak
- Auto-scroll to latest entry
- Pause scroll toggle
- Timestamp for each segment
- Speaking indicator (animated)

**Controls:**
- Start/Stop recording
- Mute/Unmute microphone
- Speaker volume controls
- Recording duration timer

**Status Indicators:**
- Connection status (WebSocket)
- Audio input level
- Processing latency
- Number of speakers detected

### Component Library Specifications

#### Core Components

**Button:**
- Primary: Solid background, white text
- Secondary: Outlined border
- Ghost: Text only with hover background
- Destructive: Red variant for delete actions
- Loading state: Spinner + disabled
- Icon support (left/right/both)
- Sizes: sm, md, lg

**Input:**
- Label above input
- Placeholder text
- Error states with message
- Success/validation indicators
- Clear button (when has value)
- RTL support for Hebrew text

**Card:**
- Subtle shadow
- Rounded corners
- Padding: 24px
- Hover effect (lift on hover)
- Clickable variant (cursor pointer)

**Modal/Dialog:**
- Backdrop overlay (blurred)
- Centered dialog
- Close button (X)
- Header, body, footer sections
- Responsive (mobile-friendly)
- ESC to close, click outside to dismiss

**Table:**
- Sortable columns
- Row selection (checkbox)
- Pagination
- Loading skeleton
- Empty state
- Responsive (stack on mobile)

**Audio Player:**
- Waveform visualization
- Play/Pause button
- Timeline scrubber
- Volume control
- Playback speed (0.5x - 2x)
- Keyboard shortcuts (spacebar, arrows)

**Transcript Viewer:**
- Virtual scrolling for performance
- Speaker color coding
- Timestamp links (click to jump)
- Search highlight
- Copy to clipboard
- Export dropdown

**Status Badge:**
- Color-coded (blue=processing, green=completed, red=failed, gray=pending)
- Icon support
- Pulsing animation for "processing"

**Skeleton Loader:**
- Animated shimmer effect
- Matches content layout
- Used during data fetching

**Empty State:**
- Illustration or icon
- Title and description
- Primary CTA button
- Secondary link (optional)

#### Advanced Components

**Speaker Assignment Card:**
- Audio snippet player (compact)
- Name input with suggestions
- Confidence indicator (progress bar)
- Match indicator (if found existing speaker)
- Assign button
- Animated on assignment success

**Live Transcript Stream:**
- Auto-scrolling container
- New entries slide in animation
- Speaker labels with color coding
- Timestamp formatting
- Pause scroll toggle
- Clear transcript button

**Meeting Timeline:**
- Horizontal timeline with speaker segments
- Color-coded by speaker
- Hover shows transcript snippet
- Click to jump to timestamp
- Zoom controls (time range selector)

**Progress Indicator:**
- Multi-step progress bar
- Current step highlighted
- Completed steps with checkmark
- Loading spinner for current step
- Estimated time remaining

### User Flows

#### Flow 1: Upload & Process Meeting

1. User clicks "New Meeting" → Upload page
2. Drags file or selects from browser
3. File preview appears → User adds title
4. Clicks "Process" → File uploads to S3
5. Redirected to meeting detail page
6. Processing status shown with progress
7. Page auto-refreshes when complete
8. User can immediately view transcript/summary

#### Flow 2: Assign Speaker Names

1. User navigates to meeting → Speakers tab
2. Sees list of unidentified speakers (SPK_1, SPK_2...)
3. Each speaker has:
   - Audio snippet (15 seconds)
   - Name suggestions (if extracted from transcript)
   - Input field for custom name
4. User plays snippet to verify
5. User either:
   - Selects suggested name (with confidence score)
   - Types custom name
6. Clicks "Assign Name"
7. Success animation
8. Speaker card updates with assigned name
9. Transcript automatically updates to show real names

#### Flow 3: Real-time Meeting Recording

1. User starts new meeting → Live Recording tab
2. Grants microphone permission
3. Clicks "Start Recording"
4. Real-time transcript appears as they speak
5. Speaker labels appear automatically
6. User can pause/resume
7. On "Stop", processing begins
8. Redirected to meeting detail with full results

#### Flow 4: Review & Export

1. User views completed meeting
2. Reviews transcript (filters by speaker if needed)
3. Assigns any remaining speaker names
4. Reviews summary
5. Clicks "Export" → Chooses format (PDF, TXT, JSON)
6. File downloads
7. Can share via link or email

### API Integration Points

**Base URL:** `https://api.hebrewmeetings.com` (or environment variable)

**Key Endpoints:**

```
POST /meetings/upload
  - Multipart form with audio file
  - Returns: { meeting_id, status, processing_task_id }

GET /meetings/{id}
  - Returns: Meeting details, status

GET /meetings/{id}/transcript
  - Returns: Speaker-labeled transcript segments

GET /meetings/{id}/unidentified_speakers
  - Returns: List of speakers with snippets and suggestions

PUT /meetings/{id}/speakers/assign
  - Body: { speaker_label, speaker_name }
  - Returns: { speaker_id, name, is_new }

GET /meetings/{id}/summary
  - Returns: AI-generated summary with key points

GET /organizations/{id}/speakers
  - Returns: List of known speakers

WebSocket: ws://api.hebrewmeetings.com/ws
  - Events: transcript:update, processing:complete
```

### Responsive Design

**Breakpoints:**
- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

**Mobile Adaptations:**
- Sidebar becomes hamburger menu
- Cards stack vertically
- Tables become cards
- Modal becomes full-screen sheet
- Audio player becomes compact inline

### Accessibility Requirements

- WCAG 2.1 AA compliance
- Keyboard navigation support
- Screen reader friendly (ARIA labels)
- Focus indicators visible
- Color contrast ratios (4.5:1 minimum)
- Alt text for all images/icons
- Semantic HTML structure
- Form labels associated correctly

### Performance Targets

- First Contentful Paint: < 1.5s
- Time to Interactive: < 3s
- Lighthouse score: > 90
- Bundle size: < 200KB initial load
- Audio playback: No stuttering, smooth scrubbing
- Transcript rendering: Handle 1000+ segments smoothly

### Internationalization

- Hebrew (RTL) and English (LTR) support
- Language switcher in header
- RTL-aware layouts and components
- Hebrew date/time formatting
- Currency formatting (if applicable)

### Error Handling

- Network errors: User-friendly message with retry
- API errors: Show specific error message
- Validation errors: Inline form errors
- 404/403 pages: Branded error pages with navigation
- Error boundary: Catch React errors gracefully

### Testing Considerations

- Component tests (Jest + React Testing Library)
- E2E tests (Playwright/Cypress)
- Visual regression tests
- Audio playback testing
- RTL layout testing
- Accessibility audit

### Animation & Micro-interactions

- Page transitions: Smooth fade (200ms)
- Button clicks: Subtle scale (1.05)
- Card hover: Lift shadow
- Loading: Skeleton → Content fade-in
- Success actions: Checkmark animation
- Error: Shake animation
- Form focus: Input border glow
- Audio playback: Waveform animation

### Dark Mode (Optional Enhancement)

- Toggle in settings
- Dark background (#1F2937)
- Light text (#F9FAFB)
- Maintain contrast ratios
- Smooth theme transition

### Implementation Priority

**Phase 1 (MVP):**
1. Authentication & Dashboard
2. Meeting Upload
3. Meeting Detail (Transcript, Summary)
4. Speaker Assignment
5. Basic Export

**Phase 2:**
1. Real-time Recording
2. Advanced Analytics
3. Speaker Management
4. Enhanced Search & Filters

**Phase 3:**
1. Collaboration Features
2. Advanced Export Options
3. Custom Templates
4. API Integration UI

### Design Inspirations

Reference these Israeli/Global SaaS products for design cues:
- **Monday.com**: Card-based layouts, colorful tags, clean filters
- **Wix**: Generous whitespace, modern typography, smooth animations
- **Fiverr**: Clean dashboard, intuitive navigation, professional aesthetics
- **Notion**: Flexible layouts, powerful editing, minimalist design
- **Linear**: Polished UI, excellent micro-interactions, modern feel

### Final Notes

- Prioritize user experience and clarity
- Make complex AI features feel simple and intuitive
- Hebrew text should be native and natural
- Performance is critical for audio/transcript handling
- Mobile experience should be fully functional, not just responsive
- Accessibility ensures all users can benefit from the tool

---

**This specification serves as the complete blueprint for building a world-class, Israeli SOTA B2B-SaaS frontend for the Hebrew Meeting Summarizer platform.**

