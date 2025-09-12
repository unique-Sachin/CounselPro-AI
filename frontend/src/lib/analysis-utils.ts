/**
 * Utility functions for analysis data processing
 */

import { SessionAnalysisResponse, BulkAnalysisItem } from './types.analysis';

interface RedFlag {
  type?: string;
  message?: string;
  description?: string;
  timestamp?: string;
}

/**
 * Filters red flags related to payment issues
 * @param flags - Array of red flags from audio analysis (can be strings or objects)
 * @returns Filtered array of payment-related flags
 */
export function filterPaymentFlags(flags: (RedFlag | string)[] = []): (RedFlag | string)[] {
  const paymentKeywords = [
    'payment',
    'billing',
    'pay on your behalf',
    'fee',
    'refund',
    'advance',
    'cost',
    'price',
    'money',
    'financial',
    'charge',
    'invoice',
    'gst',
    'catalog',
    'placement',
    'faculty'
  ];

  return flags.filter(flag => {
    if (typeof flag === 'string') {
      const flagText = flag.toLowerCase();
      return paymentKeywords.some(keyword => flagText.includes(keyword));
    } else {
      const type = (flag.type || '').toLowerCase();
      const message = (flag.message || flag.description || '').toLowerCase();
      return paymentKeywords.some(keyword => 
        type.includes(keyword) || message.includes(keyword)
      );
    }
  });
}

/**
 * Get payment verification verdict based on payment flags
 */
export function getPaymentVerdict(flags: (RedFlag | string)[]): "Verified" | "Issues Found" {
  const paymentFlags = filterPaymentFlags(flags);
  return paymentFlags.length === 0 ? "Verified" : "Issues Found";
}

/**
 * Filter pressure-related flags from red flags array
 */
export function filterPressureFlags(flags: (RedFlag | string)[] = []): (RedFlag | string)[] {
  const pressureKeywords = [
    'pressure',
    'coercion', 
    'guarantee',
    'last chance',
    'urgent',
    'must',
    'leave your job',
    'commit today'
  ];

  return flags.filter(flag => {
    if (typeof flag === 'string') {
      const flagText = flag.toLowerCase();
      return pressureKeywords.some(keyword => flagText.includes(keyword));
    } else {
      const type = (flag.type || '').toLowerCase();
      const message = (flag.message || flag.description || '').toLowerCase();
      return pressureKeywords.some(keyword => 
        type.includes(keyword) || message.includes(keyword)
      );
    }
  });
}

/**
 * Get pressure severity based on number of pressure flags
 */
export function getPressureSeverity(pressureFlags: (RedFlag | string)[]): "None" | "Low" | "Medium" | "High" {
  const count = pressureFlags.length;
  
  if (count === 0) return "None";
  if (count <= 2) return "Low";
  if (count <= 4) return "Medium";
  return "High";
}

/**
 * Calculate compliance score for a session analysis
 * @param analysis - Session analysis response or bulk analysis item
 * @returns Compliance score between 0-100
 */
export function calcCompliance(analysis: SessionAnalysisResponse): number;
export function calcCompliance(analysis: BulkAnalysisItem): number;
export function calcCompliance(analysis: SessionAnalysisResponse | BulkAnalysisItem): number {
  let score = 0;

  // Handle bulk analysis format
  if ('video_analysis_summary' in analysis) {
    const attireMeets = analysis.video_analysis_summary?.environment_analysis?.attire_assessment?.meets_professional_standards;
    const backgroundMeets = analysis.video_analysis_summary?.environment_analysis?.background_assessment?.meets_professional_standards;
    
    if (attireMeets === true) {
      score += 50;
    }
    
    if (backgroundMeets === true) {
      score += 50;
    }

    // Get red flags from audio analysis
    const redFlags = analysis.audio_analysis_summary?.red_flags || [];
    
    // Deduct for payment red flags (-25)
    const paymentFlags = filterPaymentFlags(redFlags);
    if (paymentFlags.length > 0) {
      score -= 25;
    }

    // Deduct for pressure red flags (-25)
    const pressureFlags = filterPressureFlags(redFlags);
    if (pressureFlags.length > 0) {
      score -= 25;
    }

    return Math.max(0, Math.min(100, score));
  }

  // Handle full analysis format (existing logic)
  const attireMeets = analysis.video_analysis_data?.environment_analysis?.attire_assessment?.meets_professional_standards;
  const backgroundMeets = analysis.video_analysis_data?.environment_analysis?.background_assessment?.meets_professional_standards;

  if (attireMeets === true) {
    score += 50;
  }
  
  if (backgroundMeets === true) {
    score += 50;
  }

  // Get red flags from audio analysis
  const redFlags = analysis.audio_analysis_data?.red_flags || [];
  
  // Deduct for payment red flags (-25)
  const paymentFlags = filterPaymentFlags(redFlags);
  if (paymentFlags.length > 0) {
    score -= 25;
  }

  // Deduct for pressure red flags (-25)
  const pressureFlags = filterPressureFlags(redFlags);
  if (pressureFlags.length > 0) {
    score -= 25;
  }

  // Clamp between 0-100
  return Math.max(0, Math.min(100, score));
}

/**
 * Count total red flags in a session analysis
 * @param analysis - Session analysis response
 * @returns Total number of red flags
 */
export function countRedFlags(analysis: SessionAnalysisResponse): number;
export function countRedFlags(analysis: BulkAnalysisItem): number;
export function countRedFlags(analysis: SessionAnalysisResponse | BulkAnalysisItem): number {
  // Handle bulk analysis format
  if ('audio_analysis_summary' in analysis) {
    return analysis.audio_analysis_summary?.red_flags?.length || 0;
  }
  
  // Handle full analysis format
  const audioRedFlags = analysis.audio_analysis_data?.red_flags?.length || 0;
  const legacyRedFlags = analysis.red_flags?.length || 0;
  
  // Return the higher count (in case both exist)
  return Math.max(audioRedFlags, legacyRedFlags);
}
