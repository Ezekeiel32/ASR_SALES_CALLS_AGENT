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
  private token: string | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    // Load token from localStorage if available
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token');
    }
  }

  setToken(token: string | null) {
    this.token = token;
  }

  getToken(): string | null {
    return this.token || (typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null);
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retries: number = 2
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const timeoutDuration = 30 * 1000; // 30 seconds timeout
    
    for (let attempt = 0; attempt <= retries; attempt++) {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeoutDuration);
      
      try {
      // Add Authorization header if token is available
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
        ...options.headers,
      };

      const token = this.getToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers,
      });

        clearTimeout(timeoutId);

        if (!response.ok) {
          // Handle 401/403 auth errors
          if (response.status === 401 || response.status === 403) {
            // Clear token if it's invalid
            if (typeof window !== 'undefined') {
              localStorage.removeItem('auth_token');
              localStorage.removeItem('auth_user');
            }
            this.token = null;
            throw new Error('Not authenticated. Please login again.');
          }
          
          const error = await response.text();
          throw new Error(`API error: ${response.status} - ${error}`);
        }

        return response.json();
      } catch (error) {
        clearTimeout(timeoutId);
        
        const isLastAttempt = attempt === retries;
        const isAbortError = error instanceof Error && error.name === 'AbortError';
        const isNetworkError = error instanceof TypeError && 
          (error.message.includes('Failed to fetch') || error.message.includes('ERR_TIMED_OUT'));
        
        if (isLastAttempt) {
          if (isAbortError) {
            throw new Error('Request timeout: The server took too long to respond. Please try again.');
          }
          if (isNetworkError) {
            throw new Error('Network error: Could not connect to server. Please check if the backend is running.');
          }
          throw error;
        }
        
        // Wait before retry (exponential backoff: 1s, 2s)
        await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, attempt)));
        console.debug(`Request attempt ${attempt + 1} failed, retrying...`, endpoint);
      }
    }
    
    throw new Error('Request failed after all retries');
  }

  // Health check with retry logic for cold starts
  async healthCheck(retries: number = 3, delay: number = 2000): Promise<{ status: string }> {
    const url = `${this.baseUrl}/healthz`;
    const timeoutDuration = 15 * 1000; // 15 seconds for health check (longer for cold starts)
    
    for (let attempt = 0; attempt < retries; attempt++) {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeoutDuration);
      
      try {
        const response = await fetch(url, {
          method: 'GET',
          signal: controller.signal,
          headers: {
            'Content-Type': 'application/json',
          },
        });

        clearTimeout(timeoutId);

        if (response.ok) {
          return response.json();
        }
        
        // If not OK but got response, throw error (don't retry for 4xx errors)
        if (response.status >= 400 && response.status < 500) {
          throw new Error(`Health check failed: ${response.status}`);
        }
        
        // For 5xx or network errors, fall through to retry logic
        throw new Error(`Health check failed: ${response.status}`);
      } catch (error) {
        clearTimeout(timeoutId);
        
        const isLastAttempt = attempt === retries - 1;
        const isAbortError = error instanceof Error && error.name === 'AbortError';
        const isNetworkError = error instanceof TypeError && 
          (error.message.includes('Failed to fetch') || error.message.includes('ERR_TIMED_OUT'));
        
        if (isLastAttempt) {
          if (isAbortError) {
            throw new Error('Health check timeout: Backend may be sleeping or unreachable.');
          }
          if (isNetworkError) {
            throw new Error('Network error: Could not connect to server. Please check if the backend is running.');
          }
          throw error;
        }
        
        // Wait before retry (exponential backoff: 2s, 4s, 8s)
        await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, attempt)));
        console.debug(`Health check attempt ${attempt + 1} failed, retrying...`);
      }
    }
    
    throw new Error('Health check failed after all retries');
  }

  // Upload meeting audio file with real-time progress tracking
  async uploadMeeting(
    file: File, 
    title?: string, 
    organizationId?: string,
    onProgress?: (progress: number) => void
  ): Promise<UploadMeetingResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (title) {
      formData.append('title', title);
    }
    // Organization ID is required by backend
    // Use default organization ID if not provided
    const orgId = organizationId || '00000000-0000-0000-0000-000000000001';
    formData.append('organization_id', orgId);

    // Use XMLHttpRequest for real upload progress tracking
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      
      // Track upload progress
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable && onProgress) {
          const progress = Math.round((e.loaded / e.total) * 100);
          onProgress(progress);
        }
      });

      // Handle completion
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText);
            resolve(response);
          } catch (e) {
            reject(new Error('Invalid JSON response from server'));
          }
        } else {
          let errorText = 'Unknown error';
          try {
            errorText = xhr.responseText || xhr.statusText;
          } catch {
            errorText = `HTTP ${xhr.status} ${xhr.statusText}`;
          }
          reject(new Error(`Upload failed: ${xhr.status} - ${errorText}`));
        }
      });

      // Handle errors
      xhr.addEventListener('error', () => {
        reject(new Error('Network error: Could not connect to server. Please check if the backend is running and accessible.'));
      });

      xhr.addEventListener('abort', () => {
        reject(new Error('Upload was cancelled'));
      });

      xhr.addEventListener('timeout', () => {
        reject(new Error('Upload timeout: The request took too long. Please try again or check your connection.'));
      });

      // Set timeout (10 minutes for large audio files)
      xhr.timeout = 10 * 60 * 1000;

      // Open and send request
      xhr.open('POST', `${this.baseUrl}/meetings/upload`);
      xhr.withCredentials = true; // Include credentials for CORS
      
      // Add Authorization header if token is available
      const token = this.getToken();
      if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      }
      
      // Don't set Content-Type header - browser will set it automatically with boundary for FormData
      xhr.send(formData);
    });
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

