/**
 * Utility functions for analysis data processing
 */

interface RedFlag {
  type?: string;
  message?: string;
  description?: string;
  timestamp?: string;
}

/**
 * Filters red flags related to payment issues
 * @param flags - Array of red flags from audio analysis
 * @returns Filtered array of payment-related flags
 */
export function filterPaymentFlags(flags: RedFlag[] = []): RedFlag[] {
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
    'invoice'
  ];

  return flags.filter(flag => {
    const type = (flag.type || '').toLowerCase();
    const message = (flag.message || flag.description || '').toLowerCase();
    
    return paymentKeywords.some(keyword => 
      type.includes(keyword) || message.includes(keyword)
    );
  });
}

/**
 * Get payment verification verdict based on payment flags
 */
export function getPaymentVerdict(paymentFlags: RedFlag[]): "Verified" | "Issues Found" {
  return paymentFlags.length === 0 ? "Verified" : "Issues Found";
}

/**
 * Filter pressure-related flags from red flags array
 */
export function filterPressureFlags(flags: RedFlag[] = []): RedFlag[] {
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
    const type = (flag.type || '').toLowerCase();
    const message = (flag.message || flag.description || '').toLowerCase();
    
    return pressureKeywords.some(keyword => 
      type.includes(keyword) || message.includes(keyword)
    );
  });
}

/**
 * Get pressure severity based on number of pressure flags
 */
export function getPressureSeverity(pressureFlags: RedFlag[]): "None" | "Low" | "Medium" | "High" {
  const count = pressureFlags.length;
  
  if (count === 0) return "None";
  if (count <= 2) return "Low";
  if (count <= 4) return "Medium";
  return "High";
}
