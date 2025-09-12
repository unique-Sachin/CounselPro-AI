// Session Analysis Types - Updated to match actual API response structure

export interface VideoAnalysisData {
  session_overview?: {
    total_duration?: string;
    total_participants?: number;
    overall_engagement?: {
      average_camera_on?: number;
      participants_engaged?: number;
      participants_with_issues?: number;
    };
    session_quality?: string;
  };
  participants?: Record<string, {
    participant_id?: number;
    engagement_summary?: {
      overall_status?: string;
      camera_on_percentage?: number;
      active_camera_percentage?: number;
      using_static_image?: boolean;
      static_image_percentage?: number;
    };
    session_periods?: {
      camera_on_periods?: Array<{
        start?: string;
        end?: string;
        duration_seconds?: number;
        duration_formatted?: string;
      }>;
      camera_off_periods?: Array<{
        start?: string;
        end?: string;
        duration_seconds?: number;
        duration_formatted?: string;
      }>;
      longest_continuous_on?: {
        duration_seconds?: number;
        duration_formatted?: string;
        start?: string;
        end?: string;
      } | null;
      longest_continuous_off?: {
        duration_seconds?: number;
        duration_formatted?: string;
        start?: string;
        end?: string;
      } | null;
    };
    behavior_insights?: {
      consistency_score?: number;
      engagement_pattern?: string;
      notable_issues?: string[];
    };
  }>;
  session_patterns?: {
    engagement_timeline?: Array<{
      period?: string;
      status?: string;
      duration?: string;
    }>;
    collective_off_periods?: Array<{
      start?: string;
      end?: string;
      duration_formatted?: string;
    }>;
  };
  environment_analysis?: {
    attire_assessment?: {
      overall_rating?: number;
      description?: string;
      meets_professional_standards?: boolean;
    };
    background_assessment?: {
      overall_rating?: number;
      description?: string;
      meets_professional_standards?: boolean;
    };
  };
  recommendations?: string[];
  audio_path?: string;
  technical_info?: {
    analysis_method?: string;
    total_frames_analyzed?: number;
    analysis_timestamp?: string;
  };
}

export interface CourseInfo {
  name: string;
  claimed_duration?: string;
  claimed_fee?: string;
  catalog_duration?: string;
  catalog_fee?: string;
  match_status?: 'MATCH' | 'MISMATCH';
  confidence_score?: number;
  notes?: string;
}

export interface AudioAnalysisData {
  courses_mentioned?: CourseInfo[];
  overall_summary?: string;
  accuracy_score?: number;
  red_flags?: Array<{
    type?: string;
    description?: string;
    severity?: 'low' | 'medium' | 'high' | 'critical';
    timestamp?: string;
  } | string>;
  session_metadata?: {
    session_id?: string | null;
    total_utterances?: number;
    counselor_utterances?: number;
    student_utterances?: number;
    verification_scope?: string;
    content_filtering?: string;
    original_length_words?: number;
    filtered_length_words?: number;
    estimated_tokens?: number;
    processing_method?: string;
    diarization_note?: string;
  };
}

export interface SessionAnalysisResponse {
  uid?: string;
  session_uid?: string;
  video_analysis_data?: VideoAnalysisData;
  audio_analysis_data?: AudioAnalysisData;
  created_at?: string;
  updated_at?: string;
  session?: {
    uid?: string;
    description?: string;
    session_date?: string;
    counselor?: {
      uid?: string;
      name?: string;
    };
  };
  status?: "PENDING" | "STARTED" | "COMPLETED" | "FAILED";
  progress_percentage?: number;
  
  // Legacy fields for backward compatibility
  participants?: Participant[];
  red_flags?: RedFlag[];
  emotional_analysis?: EmotionalAnalysis;
  topic_analysis?: TopicAnalysis;
  communication_metrics?: CommunicationMetrics;
  audio_analysis?: AudioAnalysisData;
  video_analysis?: VideoAnalysisData;
  session_summary?: SessionSummary;
  analysis_metadata?: {
    processing_time_seconds?: number;
    ai_model_version?: string;
    confidence_score?: number;
    data_sources?: string[];
    analysis_completeness?: number;
  };
  transcript_uid?: string;
  media_files?: Array<{
    type?: 'audio' | 'video';
    url?: string;
    duration?: number;
    format?: string;
  }>;
  errors?: Array<{
    code?: string;
    message?: string;
    timestamp?: string;
  }>;
  warnings?: string[];
}

// Legacy types for backward compatibility
export interface RedFlag {
  id?: string;
  type?: string;
  severity?: 'low' | 'medium' | 'high' | 'critical';
  description?: string;
  timestamp?: string;
  confidence?: number;
  category?: string;
  context?: string;
  recommendations?: string[];
}

export interface Participant {
  id?: string;
  name?: string;
  role?: 'counselor' | 'student' | 'other';
  speaking_time?: number;
  speaking_percentage?: number;
  interruption_count?: number;
  avg_speaking_speed?: number;
  emotional_state?: string;
  engagement_level?: number;
  participation_score?: number;
}

export interface EmotionalAnalysis {
  dominant_emotion?: string;
  emotion_distribution?: Record<string, number>;
  emotional_intensity?: number;
  emotional_stability?: number;
  mood_progression?: Array<{
    timestamp?: string;
    emotion?: string;
    intensity?: number;
  }>;
}

export interface TopicAnalysis {
  main_topics?: string[];
  topic_distribution?: Record<string, number>;
  topic_transitions?: Array<{
    from?: string;
    to?: string;
    timestamp?: string;
  }>;
  discussion_depth?: Record<string, number>;
}

export interface CommunicationMetrics {
  total_speaking_time?: number;
  silence_periods?: number;
  avg_response_time?: number;
  interruption_frequency?: number;
  question_count?: number;
  statement_count?: number;
  active_listening_indicators?: number;
}

export interface SessionSummary {
  overall_rating?: number;
  session_effectiveness?: number;
  key_outcomes?: string[];
  recommendations?: string[];
  follow_up_actions?: string[];
  session_highlights?: string[];
  areas_for_improvement?: string[];
  counselor_performance?: {
    empathy_score?: number;
    communication_effectiveness?: number;
    problem_solving_approach?: number;
    professional_conduct?: number;
  };
  student_engagement?: {
    participation_level?: number;
    receptiveness?: number;
    emotional_openness?: number;
    progress_indicators?: string[];
  };
}

// API Response wrapper
export interface SessionAnalysisApiResponse {
  success?: boolean;
  data?: SessionAnalysisResponse;
  message?: string;
  error?: string;
  status_code?: number;
}

// For React Query hooks
export interface UseSessionAnalysisOptions {
  enabled?: boolean;
  staleTime?: number;
  retry?: number;
  refetchOnWindowFocus?: boolean;
  refetchInterval?: number;
}

// Bulk Analysis Types for Dashboard
export interface BulkAnalysisItem {
  session_uid: string;
  created_at: string;
  updated_at: string;
  status?: "PENDING" | "STARTED" | "COMPLETED" | "FAILED";
  video_analysis_summary: {
    environment_analysis: {
      attire_assessment: {
        meets_professional_standards: boolean;
      };
      background_assessment: {
        meets_professional_standards: boolean;
      };
    };
  };
  audio_analysis_summary: {
    red_flags: {
      type: string;
      description: string;
      severity?: string;
    }[];
  };
}

export interface BulkAnalysisResponse {
  analyses: BulkAnalysisItem[];
}
