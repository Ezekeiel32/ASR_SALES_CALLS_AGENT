// API Client for IvriMeet Backend
let API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Ensure URL has protocol
if (API_BASE_URL && !API_BASE_URL.startsWith('http://') && !API_BASE_URL.startsWith('https://')) {
  API_BASE_URL = `https://${API_BASE_URL}`;
}

export interface Meeting {
  id: string;
  title?: string;
  status: 'completed' | 'processing' | 'failed' | 'pending';
  date?: string;
  duration?: number; // in seconds
  speaker_count?: number;
  speakers?: Speaker[];
  transcript?: string;
  transcript_segments?: Array<{
    start: number;
    end: number;
    text: string;
    speaker?: string;
    speaker_label?: string;
    speaker_id?: string | null;
  }>;
  summary?: string | object;
  created_at: string;
  organization_id: string;
}

export interface Speaker {
  id: string;
  label?: string;
  name?: string;
  organization_id?: string;
  meetings_count?: number;
  last_seen?: string;
  avatar_url?: string;
  audio_snippet_url?: string;
  confidence?: number;
  created_at?: string;
}

export interface TranscriptSegment {
  speaker_label: string;
  timestamp: string;
  text: string;
}

export interface UploadMeetingResponse {
  meeting_id: string;
  status: string;
  message: string;
}

export interface MeetingListResponse {
  meetings: Meeting[];
  total: number;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    // Add timeout for regular requests (30 seconds)
    const timeoutDuration = 30 * 1000;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutDuration);
    
    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`API error: ${response.status} - ${error}`);
      }

      return response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Request timeout: The server took too long to respond. Please try again.');
      }
      
      if (error instanceof TypeError) {
        if (error.message.includes('Failed to fetch') || error.message.includes('ERR_TIMED_OUT')) {
          throw new Error('Network error: Could not connect to server. Please check if the backend is running.');
        }
      }
      
      throw error;
    }
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/healthz');
  }

  // Upload meeting audio file with timeout handling
  async uploadMeeting(file: File, title?: string, organizationId?: string): Promise<UploadMeetingResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (title) {
      formData.append('title', title);
    }
    // Organization ID is required by backend
    // Use default organization ID if not provided
    const orgId = organizationId || '00000000-0000-0000-0000-000000000001';
    formData.append('organization_id', orgId);

    // Create AbortController for timeout (10 minutes for large audio files)
    const timeoutDuration = 10 * 60 * 1000; // 10 minutes
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutDuration);

    try {
      const response = await fetch(`${this.baseUrl}/meetings/upload`, {
        method: 'POST',
        body: formData,
        // Don't set Content-Type header - browser will set it automatically with boundary for FormData
        credentials: 'include',
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        let errorText = 'Unknown error';
        try {
          errorText = await response.text();
        } catch {
          errorText = `HTTP ${response.status} ${response.statusText}`;
        }
        throw new Error(`Upload failed: ${response.status} - ${errorText}`);
      }

      return response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Upload timeout: The request took too long. Please try again or check your connection.');
      }
      
      if (error instanceof TypeError) {
        if (error.message.includes('Failed to fetch') || error.message.includes('ERR_TIMED_OUT')) {
          throw new Error('Network error: Could not connect to server. Please check if the backend is running and accessible.');
        }
      }
      
      throw error;
    }
  }

  // List meetings
  async listMeetings(
    organizationId?: string,
    status?: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<MeetingListResponse> {
    const params = new URLSearchParams();
    if (organizationId) params.append('organization_id', organizationId);
    if (status) params.append('status', status);
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());

    const response = await this.request<MeetingListResponse>(
      `/meetings?${params.toString()}`
    );
    return response;
  }

  // Get meeting details
  async getMeeting(meetingId: string): Promise<Meeting> {
    return this.request<Meeting>(`/meetings/${meetingId}`);
  }

  // Get meeting transcript
  async getMeetingTranscript(meetingId: string): Promise<{
    meeting_id: string;
    transcript_segments: Array<{
      start: number;
      end: number;
      text: string;
      speaker: string;
      speaker_id: string | null;
    }>;
  }> {
    return this.request<{
      meeting_id: string;
      transcript_segments: Array<{
        start: number;
        end: number;
        text: string;
        speaker: string;
        speaker_id: string | null;
      }>;
    }>(`/meetings/${meetingId}/transcript`);
  }

  // Get meeting summary
  async getMeetingSummary(meetingId: string): Promise<{ 
    meeting_id: string;
    summary: string | object; // Can be string or JSON object
  }> {
    return this.request<{ 
      meeting_id: string;
      summary: string | object;
    }>(`/meetings/${meetingId}/summary`);
  }

  // Get unidentified speakers
  async getUnidentifiedSpeakers(meetingId: string): Promise<{
    meeting_id: string;
    unidentified_speakers: Record<string, Array<{
      suggestion_id: string;
      name: string;
      confidence: number;
      source_text?: string;
      accepted?: boolean;
      segment_start_time?: number;
      segment_end_time?: number;
    }>>;
  }> {
    return this.request<{
      meeting_id: string;
      unidentified_speakers: Record<string, Array<{
        suggestion_id: string;
        name: string;
        confidence: number;
        source_text?: string;
        accepted?: boolean;
        segment_start_time?: number;
        segment_end_time?: number;
      }>>;
    }>(`/meetings/${meetingId}/unidentified_speakers`);
  }

  // Assign speaker name
  async assignSpeakerName(
    meetingId: string,
    speakerLabel: string,
    name: string
  ): Promise<{ success: boolean; speaker: Speaker }> {
    return this.request<{ success: boolean; speaker: Speaker }>(
      `/meetings/${meetingId}/speakers/assign`,
      {
        method: 'PUT',
        body: JSON.stringify({ speaker_label: speakerLabel, name }),
      }
    );
  }

  // List organization speakers
  async listSpeakers(organizationId: string): Promise<{ speakers: Speaker[] }> {
    return this.request<{ speakers: Speaker[] }>(
      `/organizations/${organizationId}/speakers`
    );
  }

  // Delete meeting
  async deleteMeeting(meetingId: string, organizationId?: string): Promise<{
    meeting_id: string;
    title: string;
    status: string;
    audio_deleted: boolean;
    snippets_deleted: number;
    message: string;
  }> {
    const params = organizationId ? `?organization_id=${organizationId}` : '';
    return this.request<{
      meeting_id: string;
      title: string;
      status: string;
      audio_deleted: boolean;
      snippets_deleted: number;
      message: string;
    }>(
      `/meetings/${meetingId}${params}`,
      {
        method: 'DELETE',
      }
    );
  }

  // Analyze audio (direct transcription and summary)
  async analyzeAudio(file: File): Promise<{
    transcription: { text: string; segments: any[] };
    summary: { text: string };
  }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/analyze`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Analysis failed: ${response.status} - ${error}`);
    }

    return response.json();
  }
}

export const apiClient = new ApiClient();
export default apiClient;

