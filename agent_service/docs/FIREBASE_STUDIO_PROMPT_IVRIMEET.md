# Firebase Studio Prototyper Prompt: IvriMeet Frontend

## Project Brief

Create a state-of-the-art B2B-SaaS web application frontend for **IvriMeet** - a Hebrew meeting summarization platform with speaker-aware transcription. The design should emulate the aesthetic of leading Israeli tech companies (Wix, Monday.com, Fiverr) - clean, modern, professional, with powerful functionality.

## Core Features

### 1. Meeting Recording and Upload
Allows users to record meetings live or upload pre-recorded audio files in various formats (MP3, WAV, M4A, AAC, WebM).

### 2. Real-time Transcription with Speaker Detection
Transcribes Hebrew meetings in real-time, automatically identifying and labeling speakers. **A tool dynamically updates transcription using LLM's and prompts, improving in accuracy using provided information during the session.**

### 3. Automated Meeting Summarization
Generates concise, speaker-aware summaries of Hebrew meetings, highlighting key points, action items, and topics discussed using generative AI.

### 4. Speaker Management and Assignment
Enables users to manage speaker profiles, assign names to unidentified speakers, and improve transcription accuracy over time.

### 5. Transcript Editing and Export
Allows users to edit the meeting transcript, correct errors, and export the transcript in various formats (TXT, JSON, SRT, PDF, DOCX, Markdown).

### 6. Analytics Dashboard
Provides insights into meeting metrics, such as speaking time distribution, word frequency, and sentiment analysis.

### 7. Secure User Authentication and Organization Management
Provides secure user authentication (email/password, SSO) and organization management features.

## Design System

**Colors:**
- Primary: Teal (#14B8A6) - professional and trustworthy
- Background: Light Gray (#F9FAFB) - clean and modern
- Accent: Orange (#F59E0B) - innovative and energetic (for CTAs and highlights)
- Text: Dark gray (#111827) for body, black (#000000) for headings
- Success: #10B981 | Warning: #F59E0B | Error: #EF4444

**Typography:**
- Font: **Inter** (Google Fonts) - grotesque-style sans-serif for both headlines and body text
- Headings: Bold, 24-48px
- Body: 16px base, 14px secondary
- Line height: 1.6
- Full RTL support for Hebrew
- Note: Only Google Fonts are supported

**Spacing:**
- Generous whitespace (24px, 32px, 48px grid)
- Card-based layouts with subtle shadows (0 1px 3px rgba(0,0,0,0.1))
- Border radius: 8-12px for cards, 6px for buttons
- Consistent padding: 16px, 24px, 32px

**Icons:**
- Consistent icon set (easily recognizable and visually appealing)
- Use same icon family throughout (e.g., Heroicons, Feather, Lucide)

**Animations:**
- Subtle animations to enhance UX and provide feedback
- Transitions: 200-300ms
- Hover: Subtle scale (1.02) or color shift
- Loading: Skeleton loaders with shimmer

## Core Pages & Components

### 1. Dashboard (`/dashboard`)
- Header: IvriMeet logo, search, user menu, notifications
- Sidebar: Navigation (collapsible), meetings, speakers, settings
- Main: Meeting cards grid/list with:
  - Thumbnail/preview
  - Title with status badge
  - Date, duration, speaker count
  - Quick actions (View, Edit, Delete)
  - Hover effect with preview
- Filter bar: Date, status, tags
- Stats widget: Total meetings, minutes, speakers, accuracy
- Empty state: Illustration + "Upload First Meeting" CTA (Orange accent button)

### 2. Meeting Upload (`/meetings/new`)
**Upload Tab:**
- Drag-and-drop zone (visual feedback) - Teal border on hover
- File browser button (Orange accent)
- Supported formats: MP3, WAV, M4A, AAC, WebM
- Preview: Duration, size, waveform
- Title input, optional tags/description
- Submit button with loading state (Teal primary)

**Live Recording Tab:**
- Large "Start Recording" button (Orange accent for energy)
- Microphone permission handling
- Real-time audio level indicator (Teal waveform)
- Timer (MM:SS), Pause/Resume, Stop
- Audio preview before submission

**Real-time Transcription Enhancement:**
- Live transcript display with LLM-powered accuracy improvements
- Dynamic update mechanism using prompts and context
- User can provide corrections that feed back into the system
- Accuracy indicator showing improvement over time
- Real-time confidence scores

**Processing Status:**
- Progress bar with steps (Teal progress indicator):
  1. Uploading → 2. Transcribing → 3. Identifying Speakers → 4. Generating Summary → 5. Complete ✓
- Estimated time remaining
- Cancel option

### 3. Meeting Detail (`/meetings/[id]`)
**Header:**
- Title (editable), Status badge, Date/Duration
- Actions: Share, Export (Orange accent), Delete
- Teal accent for primary actions

**Tabs: Overview | Transcript | Speakers | Summary | Analytics**

**Overview Tab:**
- Metrics cards: Duration, Speaker count, Word count, Confidence
- Quick summary preview
- Key points bullet list
- Action items highlight
- Timeline visualization (Teal primary, Orange accents)

**Transcript Tab:**
- Scrollable viewer with virtual scrolling
- Speaker-labeled segments (color-coded - Teal variations)
- **Editable transcript** with inline editing
- Timestamp navigation (click to jump)
- Search (highlight matches - Orange highlight)
- Export dropdown (Orange CTA): TXT, JSON, SRT, PDF, DOCX, Markdown
- Audio sync (highlight current segment)
- Filter by speaker
- Copy segments
- Save edits button (Teal primary)

**Speakers Tab:**
- Grid of speaker cards, each with:
  - 15-second audio snippet player (play/pause) - Teal controls
  - Speaker label (SPK_1, SPK_2)
  - Name input with autocomplete suggestions
  - Confidence indicator (progress bar - Teal)
  - Voiceprint match indicator (if found)
  - Speaking time stats
  - "Assign Name" button (Orange accent)
- Modal on assignment: Large player, name input, confidence, save/cancel
- Assign button uses Orange accent for energy

**Summary Tab:**
- Markdown-formatted summary
- Speaker-aware sections
- Key points (expandable)
- Action items with checkboxes
- Topics/categories tags
- Sentiment indicators
- Export: PDF, DOCX, Markdown (Orange CTA buttons)

**Analytics Tab:**
- Charts and visualizations:
  - Speaking time distribution (pie chart - Teal/Orange palette)
  - Timeline heatmap
  - Word frequency
  - Sentiment over time
  - Topics/entities extraction
- Interactive charts (zoom, filter)
- Teal primary colors, Orange for highlights

### 4. Speaker Management (`/speakers`)
- Grid of speaker profiles
- Cards: Avatar, Name, Organization, Meeting count, Last seen, Confidence
- Search and filter
- Detail view: Profile, Stats, Associated meetings, Voiceprint details
- Teal primary for cards, Orange for actions

### 5. Real-time Meeting (`/meetings/[id]/live`)
- Real-time scrolling transcript
- **LLM-powered dynamic updates** - accuracy improves during session
- Speaker labels appear as they speak
- Auto-scroll toggle
- Timestamp per segment
- Speaking indicator (animated - Teal pulse)
- Controls: Start/Stop (Orange), Mute, Volume, Timer
- Status: Connection, Audio level (Teal indicator), Latency, Speaker count
- Live accuracy improvement indicator showing system learning in real-time

### 6. Settings (`/settings`)
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

## Component Specifications

**Button:**
- Primary: Teal (#14B8A6) background, white text
- Secondary: Outlined Teal border
- Accent: Orange (#F59E0B) for CTAs and highlights
- Ghost: Text only with hover background
- Destructive: Red variant for delete actions
- Loading state: Spinner + disabled
- Icon support (left/right/both)
- Sizes: sm, md, lg

**Input:**
- Label above input
- Placeholder text
- Error states with message
- Success/validation indicators (Teal checkmark)
- Clear button (when has value)
- RTL support for Hebrew text
- Focus state: Teal border

**Card:**
- Subtle shadow on light gray background
- Rounded corners (8-12px)
- Padding: 24px
- Hover effect (lift on hover - subtle animation)
- Clickable variant (cursor pointer)
- Background: White on light gray (#F9FAFB) page

**Modal/Dialog:**
- Backdrop overlay (blurred, light gray tint)
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
- Waveform visualization (Teal primary)
- Play/Pause button (Teal)
- Timeline scrubber (Teal track, Orange handle)
- Volume control
- Playback speed (0.5x - 2x)
- Keyboard shortcuts (spacebar, arrows)

**Transcript Viewer:**
- Virtual scrolling for performance
- Speaker color coding (Teal variations)
- Timestamp links (click to jump)
- Search highlight (Orange)
- Copy to clipboard
- Export dropdown (Orange CTA)
- **Inline editing** with save button (Teal)

**Status Badge:**
- Color-coded: Teal=processing, Green=completed, Red=failed, Gray=pending
- Icon support
- Pulsing animation for "processing" (Teal pulse)

**Skeleton Loader:**
- Animated shimmer effect (light gray background)
- Matches content layout
- Used during data fetching

**Empty State:**
- Illustration or icon
- Title and description
- Primary CTA button (Orange accent)
- Secondary link (Teal)

## Key User Flows

**Flow 1: Upload Meeting**
1. Click "New Meeting" (Orange button) → Upload page
2. Drag file or select
3. Preview → Add title
4. Process → Upload to S3
5. Redirect to detail → Show processing progress (Teal progress bar)
6. Auto-refresh on complete → View results

**Flow 2: Live Recording with Real-time Enhancement**
1. Start meeting → Live Recording tab
2. Grant mic permission
3. Start recording (Orange button)
4. Real-time transcript appears with LLM-powered improvements
5. System dynamically updates accuracy using context
6. User can provide corrections that improve system
7. Speaker labels auto-detect
8. Stop → Processing → Full results

**Flow 3: Assign Speaker Names**
1. Navigate to Speakers tab
2. View unidentified speakers (SPK_1, SPK_2...)
3. Each shows: Audio snippet, Name suggestions, Input field
4. Play snippet → Verify
5. Select suggestion OR type custom name
6. Click "Assign" (Orange button) → Success animation
7. Card updates → Transcript shows real names

**Flow 4: Edit and Export Transcript**
1. User views completed meeting → Transcript tab
2. Clicks edit button (Teal)
3. Inline editing mode activated
4. Makes corrections inline
5. Saves edits (Teal save button)
6. Clicks Export (Orange) → Chooses format (PDF, TXT, JSON, SRT, DOCX, Markdown)
7. File downloads

## Technical Requirements

**Framework:** Next.js 14+ (App Router), TypeScript, React 18+, Tailwind CSS

**State:** Zustand (global), React Query (server), Local state (UI)

**Libraries:**
- Shadcn/ui or Radix UI for accessible components
- Framer Motion for animations
- React Hook Form + Zod for forms
- React Audio Player or Wavesurfer.js for audio playback
- Socket.io-client for WebSocket real-time updates
- RecordRTC or MediaRecorder API for audio capture
- Axios or Fetch for API calls
- date-fns for date formatting
- i18next for internationalization (Hebrew/English)

**Fonts:**
- **Inter from Google Fonts** (only Google Fonts supported)
- Proper Hebrew RTL support with Alef or Assistant as fallback (if needed)

**Responsive:**
- Mobile (<640px): Sidebar becomes hamburger, cards stack
- Tablet (640-1024px): Adaptive layout
- Desktop (>1024px): Full layout

**Accessibility:**
- WCAG 2.1 AA compliance
- Keyboard navigation support
- Screen reader friendly (ARIA labels)
- Focus indicators visible (Teal focus ring)
- Color contrast ratios (4.5:1 minimum)
- Alt text for all images/icons
- Semantic HTML structure

**Performance:**
- First Contentful Paint: <1.5s
- Time to Interactive: <3s
- Lighthouse score: >90
- Bundle size: <200KB initial load
- Audio playback: No stuttering, smooth scrubbing
- Transcript rendering: Handle 1000+ segments smoothly

## API Integration

**Base:** `https://api.ivrimeet.com` (or environment variable)

**Key Endpoints:**
- `POST /meetings/upload` - Upload audio
- `GET /meetings/{id}` - Get details
- `GET /meetings/{id}/transcript` - Get transcript
- `PUT /meetings/{id}/transcript` - **Edit transcript**
- `GET /meetings/{id}/unidentified_speakers` - Get speakers + snippets
- `PUT /meetings/{id}/speakers/assign` - Assign name
- `GET /meetings/{id}/summary` - Get summary
- `POST /meetings/{id}/export` - Export transcript (format param)
- `WebSocket ws://api.../ws` - Real-time updates with LLM improvements

**Real-time Enhancement Endpoint:**
- `POST /meetings/{id}/transcription/enhance` - Provide corrections for LLM learning
- `GET /meetings/{id}/transcription/accuracy` - Get accuracy improvement metrics

## Implementation Priority

**MVP (Phase 1):**
1. Auth & Dashboard
2. Meeting Upload
3. Meeting Detail (Transcript with editing, Summary)
4. Speaker Assignment
5. Basic Export

**Phase 2:**
1. Real-time Recording with LLM enhancement
2. Analytics Dashboard
3. Speaker Management
4. Advanced Search & Filters

**Phase 3:**
1. Collaboration Features
2. Advanced Export Options
3. Custom Templates
4. API Integration UI

## Design Inspiration

Reference these Israeli/Global SaaS products for design cues:
- **Monday.com**: Card-based layouts, colorful tags, clean filters
- **Wix**: Generous whitespace, modern typography, smooth animations
- **Fiverr**: Clean dashboard, intuitive navigation, professional aesthetics
- **Notion**: Flexible layouts, powerful editing, minimalist design
- **Linear**: Polished UI, excellent micro-interactions, modern feel

**IvriMeet Brand Identity:**
- Professional yet approachable
- Innovative (Orange accents for energy)
- Trustworthy (Teal primary for reliability)
- Modern (Inter font, clean layouts)
- Hebrew-first (RTL support, cultural awareness)

## Color Usage Guidelines

**Teal (#14B8A6):**
- Primary actions (Save, Submit, Confirm)
- Progress indicators
- Active states
- Links
- Primary buttons
- Cards and highlights

**Orange (#F59E0B):**
- Call-to-action buttons (Upload, Export, Start Recording)
- Highlights and important notices
- Accent elements
- Energy and innovation cues
- Secondary CTAs

**Light Gray (#F9FAFB):**
- Page backgrounds
- Card backgrounds (white on this)
- Subtle dividers
- Disabled states

**Dark Gray/Black:**
- Body text (#111827)
- Headings (#000000)
- Icons and UI elements

## Final Notes

- **IvriMeet** brand name should be prominently displayed
- Hebrew RTL support is critical
- Real-time LLM transcription enhancement is a key differentiator - highlight this feature
- Audio playback must be smooth
- Transcript editing should feel natural and responsive
- Mobile experience fully functional
- Accessibility ensures universal usability
- Complex AI features feel simple and intuitive
- Use **Inter font from Google Fonts exclusively**
- Maintain consistent Teal primary and Orange accent throughout
- Light gray (#F9FAFB) background creates clean, modern feel
- Generous whitespace and card-based layouts for organization

---

**Create this frontend for IvriMeet with attention to detail, smooth animations, and a professional Israeli tech company aesthetic. Focus on clarity, performance, excellent user experience, and the innovative real-time transcription enhancement feature.**

