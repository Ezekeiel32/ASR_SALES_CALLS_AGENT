# Firebase Studio Prototyper Prompt: Hebrew Meeting Summarizer Frontend

## Project Brief

Create a state-of-the-art B2B-SaaS web application frontend for a Hebrew meeting summarization platform with speaker-aware transcription. The design should emulate the aesthetic of leading Israeli tech companies (Wix, Monday.com, Fiverr) - clean, modern, professional, with powerful functionality.

## Design System

**Colors:**
- Primary: Deep Blue (#1E3A8A) or Teal (#14B8A6)
- Accent: Purple (#7C3AED) or Orange (#F59E0B)
- Background: White (#FFFFFF) with subtle grays (#F9FAFB, #F3F4F6)
- Text: Dark gray (#111827) for body, black (#000000) for headings
- Success: #10B981 | Warning: #F59E0B | Error: #EF4444

**Typography:**
- Font: Inter or SF Pro (Hebrew: Alef, Assistant, Varela Round)
- Headings: Bold, 24-48px
- Body: 16px base, 14px secondary
- Line height: 1.6
- Full RTL support for Hebrew

**Spacing:**
- Grid: 24px, 32px, 48px
- Card padding: 24px
- Border radius: 8-12px for cards, 6px for buttons
- Shadows: Subtle (0 1px 3px rgba(0,0,0,0.1))

**Animations:**
- Transitions: 200-300ms
- Hover: Subtle scale (1.02) or color shift
- Loading: Skeleton loaders with shimmer

## Core Pages & Components

### 1. Dashboard (`/dashboard`)
- Header: Logo, search, user menu, notifications
- Sidebar: Navigation (collapsible), meetings, speakers, settings
- Main: Meeting cards grid/list with:
  - Thumbnail/preview
  - Title with status badge
  - Date, duration, speaker count
  - Quick actions (View, Edit, Delete)
  - Hover effect with preview
- Filter bar: Date, status, tags
- Stats widget: Total meetings, minutes, speakers, accuracy
- Empty state: Illustration + "Upload First Meeting" CTA

### 2. Meeting Upload (`/meetings/new`)
**Upload Tab:**
- Drag-and-drop zone (visual feedback)
- File browser button
- Supported formats: MP3, WAV, M4A, AAC
- Preview: Duration, size, waveform
- Title input, optional tags/description
- Submit button with loading state

**Live Recording Tab:**
- Large "Start Recording" button
- Microphone permission handling
- Real-time audio level indicator
- Timer (MM:SS), Pause/Resume, Stop
- Audio preview before submission

**Processing Status:**
- Progress bar with steps:
  1. Uploading → 2. Transcribing → 3. Identifying Speakers → 4. Generating Summary → 5. Complete ✓
- Estimated time remaining
- Cancel option

### 3. Meeting Detail (`/meetings/[id]`)
**Header:**
- Title (editable), Status badge, Date/Duration
- Actions: Share, Export, Delete

**Tabs: Overview | Transcript | Speakers | Summary | Analytics**

**Overview Tab:**
- Metrics cards: Duration, Speaker count, Word count, Confidence
- Quick summary preview
- Key points bullet list
- Action items highlight
- Timeline visualization

**Transcript Tab:**
- Scrollable viewer with virtual scrolling
- Speaker-labeled segments (color-coded)
- Timestamp navigation (click to jump)
- Search (highlight matches)
- Export: TXT, JSON, SRT
- Audio sync (highlight current segment)
- Filter by speaker
- Copy segments

**Speakers Tab:**
- Grid of speaker cards, each with:
  - 15-second audio snippet player (play/pause)
  - Speaker label (SPK_1, SPK_2)
  - Name input with autocomplete suggestions
  - Confidence indicator (progress bar)
  - Voiceprint match indicator (if found)
  - Speaking time stats
  - "Assign Name" button
- Modal on assignment: Large player, name input, confidence, save/cancel

**Summary Tab:**
- Markdown-formatted summary
- Speaker-aware sections
- Key points (expandable)
- Action items with checkboxes
- Topics/categories tags
- Sentiment indicators
- Export: PDF, DOCX, Markdown

**Analytics Tab:**
- Speaking time pie chart
- Timeline heatmap
- Word frequency
- Sentiment over time
- Interactive charts

### 4. Speaker Management (`/speakers`)
- Grid of speaker profiles
- Cards: Avatar, Name, Organization, Meeting count, Last seen, Confidence
- Search and filter
- Detail view: Profile, Stats, Associated meetings, Voiceprint details

### 5. Real-time Meeting (`/meetings/[id]/live`)
- Real-time scrolling transcript
- Speaker labels appear as they speak
- Auto-scroll toggle
- Timestamp per segment
- Speaking indicator (animated)
- Controls: Start/Stop, Mute, Volume, Timer
- Status: Connection, Audio level, Latency, Speaker count

## Component Specifications

**Button:** Primary (solid), Secondary (outlined), Ghost (text), Destructive (red), Loading state, Icons, Sizes (sm/md/lg)

**Input:** Label above, Placeholder, Error states, Success indicators, Clear button, RTL support

**Card:** Shadow, Rounded, 24px padding, Hover lift, Clickable variant

**Modal:** Backdrop blur, Centered, Close button, Header/Body/Footer, Responsive, ESC to close

**Audio Player:** Waveform, Play/Pause, Timeline scrubber, Volume, Speed (0.5x-2x), Keyboard shortcuts

**Transcript Viewer:** Virtual scroll, Speaker colors, Timestamp links, Search highlight, Copy, Export

**Status Badge:** Colors (blue=processing, green=completed, red=failed), Icon, Pulsing for "processing"

## Key User Flows

**Flow 1: Upload Meeting**
1. Click "New Meeting" → Upload page
2. Drag file or select
3. Preview → Add title
4. Process → Upload to S3
5. Redirect to detail → Show processing progress
6. Auto-refresh on complete → View results

**Flow 2: Assign Speaker Names**
1. Navigate to Speakers tab
2. View unidentified speakers (SPK_1, SPK_2...)
3. Each shows: Audio snippet, Name suggestions, Input field
4. Play snippet → Verify
5. Select suggestion OR type custom name
6. Click "Assign" → Success animation
7. Card updates → Transcript shows real names

**Flow 3: Live Recording**
1. Start meeting → Live Recording tab
2. Grant mic permission
3. Start recording
4. Real-time transcript appears
5. Speaker labels auto-detect
6. Pause/Resume available
7. Stop → Processing → Full results

## Technical Requirements

**Framework:** Next.js 14+ (App Router), TypeScript, React 18+, Tailwind CSS

**State:** Zustand (global), React Query (server), Local state (UI)

**Libraries:** Shadcn/ui, Framer Motion, React Hook Form + Zod, React Audio Player/Wavesurfer, Socket.io-client, RecordRTC, Axios

**Responsive:** Mobile (<640px), Tablet (640-1024px), Desktop (>1024px)

**Accessibility:** WCAG 2.1 AA, Keyboard nav, Screen readers, Focus indicators, Color contrast (4.5:1)

**Performance:** FCP <1.5s, TTI <3s, Lighthouse >90, Bundle <200KB

## API Integration

**Base:** `https://api.hebrewmeetings.com`

**Key Endpoints:**
- `POST /meetings/upload` - Upload audio
- `GET /meetings/{id}` - Get details
- `GET /meetings/{id}/transcript` - Get transcript
- `GET /meetings/{id}/unidentified_speakers` - Get speakers + snippets
- `PUT /meetings/{id}/speakers/assign` - Assign name
- `GET /meetings/{id}/summary` - Get summary
- `WebSocket ws://api.../ws` - Real-time updates

## Implementation Priority

**MVP (Phase 1):**
1. Auth & Dashboard
2. Meeting Upload
3. Meeting Detail (Transcript, Summary)
4. Speaker Assignment
5. Basic Export

**Phase 2:** Real-time Recording, Analytics, Speaker Management, Advanced Search

**Phase 3:** Collaboration, Advanced Export, Templates, API UI

## Design Inspiration

Reference: Monday.com (cards, colors), Wix (whitespace, typography), Fiverr (navigation, aesthetics), Notion (layouts), Linear (polish, micro-interactions)

## Final Notes

- Hebrew RTL support is critical
- Audio playback must be smooth
- Transcript rendering handles 1000+ segments
- Mobile experience fully functional
- Accessibility ensures universal usability
- Complex AI features feel simple and intuitive

---

**Create this frontend with attention to detail, smooth animations, and a professional Israeli tech company aesthetic. Focus on clarity, performance, and excellent user experience.**

