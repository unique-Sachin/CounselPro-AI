import os
from datetime import datetime

MIN_OFF_PERIOD_DURATION = int(os.getenv("MIN_OFF_PERIOD_DURATION", "6"))  # Minimum seconds for significant off period


class VideoResponse:
    
    def _format_ui_friendly_results(self, camera_analysis, attire_analysis, video_metadata, audio_path):
        """Format analysis results in a UI-friendly structure with comprehensive error handling"""
        
        try:
            # Validate input data structure
            if not self._validate_camera_analysis(camera_analysis):
                raise ValueError("Invalid camera analysis data structure")
            
            if not self._validate_attire_analysis(attire_analysis):
                raise ValueError("Invalid attire analysis data structure")
            
            # Process participant data
            participants = {}
            person_timelines = camera_analysis['detailed_results']['person_timelines']
            person_stats = camera_analysis['detailed_results']['person_stats']
            
            for person_id, stats in person_stats.items():
                periods = self._group_consecutive_periods(person_timelines.get(person_id, []))
                participants[f"person_{person_id}"] = self._format_participant_data(person_id, stats, periods)

            # Generate recommendations
            recommendations = self._generate_recommendations(participants, attire_analysis)
            
            # Create session overview
            session_overview = self._create_session_overview(camera_analysis, video_metadata, participants)
            
            # Create session patterns
            overall_periods = self._group_consecutive_periods(camera_analysis['detailed_results']['camera_timeline'])
            session_patterns = self._create_session_patterns(overall_periods, camera_analysis)
            
        except Exception as e:
            # Clean up any partial processing and re-raise with clear error
            raise ValueError(f"Failed to format video analysis results: {str(e)}") from e

        return {
            'session_overview': session_overview,
            'participants': participants,
            'session_patterns': session_patterns,
            'environment_analysis': {
                'attire_assessment': {
                    'overall_rating': attire_analysis.attire_percentage,
                    'description': attire_analysis.attire_analysis,
                    'meets_professional_standards': attire_analysis.attire_percentage >= 70
                },
                'background_assessment': {
                    'overall_rating': attire_analysis.background_percentage,
                    'description': attire_analysis.background_analysis,
                    'meets_professional_standards': attire_analysis.background_percentage >= 70
                }
            },
            'recommendations': recommendations,
            'audio_path': audio_path,
            'technical_info': {
                'analysis_method': 'YOLO + Gemini',
                'total_frames_analyzed': camera_analysis['summary']['total_samples_analyzed'],
                'analysis_timestamp': datetime.now().isoformat()
            }
        }

    def _group_consecutive_periods(self, timeline):
        """Group consecutive on/off periods for cleaner UI display"""
        periods = []
        current_period = None
        
        for event in timeline:
            status = 'on' if event['camera_on'] else 'off'
            timestamp = event['timestamp']
            
            if current_period is None or current_period['status'] != status:
                # End previous period
                if current_period is not None:
                    current_period['end_time'] = timestamp
                    current_period['duration'] = timestamp - current_period['start_time']
                    current_period['end_formatted'] = self._format_timestamp(timestamp)
                    
                    # Only add significant periods
                    min_duration = 10 if current_period['status'] == 'on' else MIN_OFF_PERIOD_DURATION
                    if current_period['duration'] >= min_duration:
                        periods.append(current_period)
                
                # Start new period
                current_period = {
                    'status': status,
                    'start_time': timestamp,
                    'start_formatted': self._format_timestamp(timestamp),
                    'end_time': None,
                    'duration': 0
                }
        
        # Close final period
        if current_period is not None:
            final_time = timeline[-1]['timestamp'] if timeline else 0
            current_period['end_time'] = final_time
            current_period['duration'] = final_time - current_period['start_time']
            current_period['end_formatted'] = self._format_timestamp(final_time)
            
            min_duration = 10 if current_period['status'] == 'on' else MIN_OFF_PERIOD_DURATION
            if current_period['duration'] >= min_duration:
                periods.append(current_period)
        
        return periods

    def _format_participant_data(self, person_id, stats, periods):
        """Format individual participant data"""
        on_periods = [p for p in periods if p['status'] == 'on']
        off_periods = [p for p in periods if p['status'] == 'off']
        
        longest_on = max(on_periods, key=lambda x: x['duration'], default={'duration': 0})
        longest_off = max(off_periods, key=lambda x: x['duration'], default={'duration': 0})
        
        # Determine engagement status
        engagement_status = 'engaged' if stats['camera_on_percentage'] > 70 else \
                           'partially_engaged' if stats['camera_on_percentage'] > 30 else 'disengaged'
        
        # Calculate consistency score
        consistency_score = 100 if not off_periods else max(0, 100 - len(off_periods) * 10)
        
        # Determine engagement pattern
        if len(off_periods) == 0:
            pattern = "fully_engaged"
        elif len(off_periods) <= 2:
            pattern = "mostly_engaged"
        elif len(off_periods) <= 5:
            pattern = "intermittently_engaged"
        else:
            pattern = "frequently_interrupted"
        
        # Identify issues
        issues = []
        if stats['camera_on_percentage'] < 50:
            issues.append("Low camera engagement")
        if stats.get('using_static_image', False):
            issues.append("Using static image")
        if len([p for p in off_periods if p['duration'] > 300]) > 0:
            issues.append("Extended absence periods")
        if len([p for p in off_periods if p['duration'] > 30]) > 5:
            issues.append("Frequent interruptions")

        return {
            'participant_id': person_id,
            'engagement_summary': {
                'overall_status': engagement_status,
                'camera_on_percentage': round(stats['camera_on_percentage'], 1),
                'active_camera_percentage': round(stats['camera_active_percentage'], 1),
                'using_static_image': stats.get('using_static_image', False),
                'static_image_percentage': round(stats.get('camera_static_percentage', 0), 1)
            },
            'session_periods': {
                'camera_on_periods': [
                    {
                        'start': p['start_formatted'],
                        'end': p['end_formatted'],
                        'duration_seconds': round(p['duration'], 1),
                        'duration_formatted': self._format_duration(p['duration'])
                    } for p in on_periods
                ],
                'camera_off_periods': [
                    {
                        'start': p['start_formatted'],
                        'end': p['end_formatted'],
                        'duration_seconds': round(p['duration'], 1),
                        'duration_formatted': self._format_duration(p['duration'])
                    } for p in off_periods
                ],
                'longest_continuous_on': {
                    'duration_seconds': round(longest_on['duration'], 1),
                    'duration_formatted': self._format_duration(longest_on['duration']),
                    'start': longest_on.get('start_formatted', 'N/A'),
                    'end': longest_on.get('end_formatted', 'N/A')
                } if longest_on['duration'] > 0 else None,
                'longest_continuous_off': {
                    'duration_seconds': round(longest_off['duration'], 1),
                    'duration_formatted': self._format_duration(longest_off['duration']),
                    'start': longest_off.get('start_formatted', 'N/A'),
                    'end': longest_off.get('end_formatted', 'N/A')
                } if longest_off['duration'] > MIN_OFF_PERIOD_DURATION else None
            },
            'behavior_insights': {
                'consistency_score': consistency_score,
                'engagement_pattern': pattern,
                'notable_issues': issues
            }
        }

    def _create_session_overview(self, camera_analysis, video_metadata, participants):
        """Create session overview data"""
        avg_engagement = camera_analysis['summary']['camera_on_percentage']
        issues_count = sum(len(p['behavior_insights']['notable_issues']) for p in participants.values())
        
        if avg_engagement >= 80 and issues_count == 0:
            session_quality = "excellent"
        elif avg_engagement >= 60 and issues_count <= 2:
            session_quality = "good"
        elif avg_engagement >= 40:
            session_quality = "fair"
        else:
            session_quality = "poor"

        return {
            'total_duration': self._format_duration(video_metadata['duration']),
            'total_participants': len(participants),
            'overall_engagement': {
                'average_camera_on': round(avg_engagement, 1),
                'participants_engaged': len([p for p in participants.values() 
                                           if p['engagement_summary']['overall_status'] == 'engaged']),
                'participants_with_issues': len([p for p in participants.values() 
                                               if p['behavior_insights']['notable_issues']])
            },
            'session_quality': session_quality
        }

    def _create_session_patterns(self, overall_periods, camera_analysis):
        """Create session-wide pattern data"""
        return {
            'engagement_timeline': [
                {
                    'period': f"{p['start_formatted']} - {p['end_formatted']}",
                    'status': p['status'],
                    'duration': self._format_duration(p['duration'])
                } for p in overall_periods if p['duration'] >= 30
            ],
            'collective_off_periods': [
                {
                    'start': p['start_formatted'],
                    'end': p['end_formatted'],
                    'duration_formatted': self._format_duration(p['duration'])
                } for p in camera_analysis['detailed_results']['off_periods']
            ]
        }

    def _generate_recommendations(self, participants, attire_analysis):
        """Generate actionable recommendations"""
        recommendations = []
        
        low_engagement_count = len([p for p in participants.values() 
                                   if p['engagement_summary']['camera_on_percentage'] < 50])
        if low_engagement_count > 0:
            recommendations.append({
                'category': 'engagement',
                'priority': 'high',
                'title': 'Improve Camera Engagement',
                'description': f"{low_engagement_count} participant(s) had low camera engagement."
            })
        
        static_users = [p for p in participants.values() 
                       if p['engagement_summary']['using_static_image']]
        if static_users:
            recommendations.append({
                'category': 'technical',
                'priority': 'medium',
                'title': 'Address Static Image Usage',
                'description': f"{len(static_users)} participant(s) using static images."
            })
        
        if attire_analysis.attire_percentage < 70:
            recommendations.append({
                'category': 'professional',
                'priority': 'low',
                'title': 'Professional Attire Guidelines',
                'description': 'Consider sharing professional attire guidelines.'
            })

        return recommendations

    def _format_duration(self, seconds):
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds//60)}m {int(seconds%60)}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"


    def _format_timestamp(self, timestamp: float) -> str:
        """Format timestamp as MM:SS"""
        return f"{int(timestamp//60):02d}:{int(timestamp%60):02d}"
    
    def _validate_camera_analysis(self, camera_analysis):
        """Validate camera analysis data structure"""
        try:
            if not isinstance(camera_analysis, dict):
                return False
            
            # Check required top-level keys
            required_keys = ['success', 'detailed_results', 'summary']
            if not all(key in camera_analysis for key in required_keys):
                return False
            
            # Check if analysis was successful
            if not camera_analysis.get('success', False):
                return False
            
            # Validate detailed_results structure
            detailed_results = camera_analysis['detailed_results']
            required_detailed_keys = ['person_timelines', 'person_stats', 'camera_timeline', 'off_periods']
            if not all(key in detailed_results for key in required_detailed_keys):
                return False
            
            # Validate summary structure
            summary = camera_analysis['summary']
            required_summary_keys = ['camera_on_percentage', 'total_samples_analyzed']
            if not all(key in summary for key in required_summary_keys):
                return False
            
            # Validate off_periods have required fields
            for period in detailed_results['off_periods']:
                if not all(key in period for key in ['start_formatted', 'end_formatted', 'duration']):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _validate_attire_analysis(self, attire_analysis):
        """Validate attire analysis data structure"""
        try:
            if attire_analysis is None:
                return False
            
            # Check required attributes
            required_attrs = ['attire_percentage', 'attire_analysis', 'background_percentage', 'background_analysis']
            return all(hasattr(attire_analysis, attr) for attr in required_attrs)
            
        except Exception:
            return False