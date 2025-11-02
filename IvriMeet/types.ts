// Import from API service for consistency
import type { Meeting as ApiMeeting, Speaker as ApiSpeaker, TranscriptSegment as ApiTranscriptSegment } from './services/api';

export enum MeetingStatus {
  Completed = 'הושלם',
  Processing = 'בעיבוד',
  Failed = 'נכשל',
}

export interface TranscriptSegment {
  speakerLabel: string;
  timestamp: string; // e.g., "00:15"
  text: string;
}

export interface Speaker {
  id: string;
  label: string; // e.g. SPK_1
  name?: string;
  meetings?: number;
  lastSeen?: Date | string;
  avatarUrl?: string;
  // For speaker assignment card
  audioSnippetUrl?: string; 
  confidence?: number;
}

export interface Meeting {
  id: string;
  title?: string;
  status: MeetingStatus | 'completed' | 'processing' | 'failed';
  date: Date | string;
  duration?: number; // in minutes
  speakerCount?: number;
  speakers?: Speaker[];
  transcript?: string;
  transcriptSegments?: TranscriptSegment[];
  unassignedSpeakers?: Speaker[];
  summary?: string;
}

// Helper functions to convert API types to UI types
export function apiMeetingToUIMeeting(apiMeeting: ApiMeeting): Meeting {
  return {
    id: apiMeeting.id,
    title: apiMeeting.title || 'פגישה ללא כותרת',
    status: mapApiStatusToUIStatus(apiMeeting.status),
    date: new Date(apiMeeting.date || apiMeeting.created_at),
    duration: apiMeeting.duration,
    speakerCount: apiMeeting.speaker_count,
    speakers: apiMeeting.speakers?.map(apiSpeakerToUISpeaker),
    transcript: apiMeeting.transcript,
    transcriptSegments: apiMeeting.transcript_segments?.map(seg => ({
      speakerLabel: seg.speaker_label,
      timestamp: seg.timestamp,
      text: seg.text,
    })),
    summary: apiMeeting.summary,
  };
}

function mapApiStatusToUIStatus(status: string): MeetingStatus {
  switch (status) {
    case 'completed': return MeetingStatus.Completed;
    case 'processing': return MeetingStatus.Processing;
    case 'failed': return MeetingStatus.Failed;
    default: return MeetingStatus.Processing;
  }
}

function apiSpeakerToUISpeaker(apiSpeaker: ApiSpeaker): Speaker {
  return {
    id: apiSpeaker.id,
    label: apiSpeaker.label,
    name: apiSpeaker.name,
    meetings: apiSpeaker.meetings_count,
    lastSeen: apiSpeaker.last_seen ? new Date(apiSpeaker.last_seen) : undefined,
    avatarUrl: apiSpeaker.avatar_url || `https://i.pravatar.cc/150?u=${apiSpeaker.id}`,
    audioSnippetUrl: apiSpeaker.audio_snippet_url,
    confidence: apiSpeaker.confidence,
  };
}