"use client";

import { CreditCard, CheckCircle, XCircle, Clock } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface RedFlag {
  type?: string;
  message?: string;
  description?: string;
  timestamp?: string;
}

interface AudioAnalysisData {
  red_flags?: (RedFlag | string)[];
}

interface PaymentVerificationCardProps {
  audioAnalysisData?: AudioAnalysisData;
}

// Helper function to filter payment-related flags from both string and object formats
function filterPaymentFlags(flags: (RedFlag | string)[] = []): (RedFlag | string)[] {
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

// Helper function to get payment verification verdict
function getPaymentVerdict(flags: (RedFlag | string)[]): "Verified" | "Issues Found" {
  const paymentFlags = filterPaymentFlags(flags);
  return paymentFlags.length === 0 ? "Verified" : "Issues Found";
}

export default function PaymentVerificationCard({ audioAnalysisData }: PaymentVerificationCardProps) {
  // If no audio analysis data, show pending state
  if (!audioAnalysisData) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <CreditCard className="h-5 w-5" />
            Payment Verification
          </CardTitle>
          <CardDescription>
            Payment status and billing verification
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-muted rounded-full flex items-center justify-center">
              <CreditCard className="h-8 w-8 text-muted-foreground" />
            </div>
            <p className="text-muted-foreground mb-2">Verification Pending</p>
            <p className="text-xs text-muted-foreground">
              Payment verification results will appear here
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Extract and filter payment-related flags
  const redFlags = audioAnalysisData.red_flags ?? [];
  const paymentFlags = filterPaymentFlags(redFlags);
  const verdict = getPaymentVerdict(redFlags);

  return (
    <Card className="h-fit">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <CreditCard className="h-5 w-5" />
          Payment Verification
        </CardTitle>
        <CardDescription>
          Payment status and billing verification
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-4">
          {/* Verification Status */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {verdict === 'Verified' ? (
                <CheckCircle className="h-5 w-5 text-green-600" />
              ) : (
                <XCircle className="h-5 w-5 text-red-600" />
              )}
              <span className="font-medium">
                {verdict}
              </span>
            </div>
            <Badge variant={verdict === 'Verified' ? 'default' : 'destructive'}>
              {verdict}
            </Badge>
          </div>

          {/* Verdict Message */}
          <p className="text-sm text-muted-foreground">
            {verdict === 'Verified' ? 'Payment verification successful' : 'Payment verification found issues'}
          </p>

          {/* Payment Issues List */}
          {paymentFlags.length > 0 && (
            <div className="space-y-3 pt-2 border-t">
              <span className="text-sm font-medium">Payment-Related Issues</span>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {paymentFlags.slice(0, 5).map((flag, index) => (
                  <div key={index} className="flex items-start gap-2 p-2 border rounded-lg bg-red-50 border-red-200">
                    <XCircle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 space-y-1 min-w-0">
                      {typeof flag === 'object' && flag.type && (
                        <div className="text-xs font-medium text-red-700 break-words">
                          {flag.type}
                        </div>
                      )}
                      <div className="text-sm text-red-800 break-words">
                        {typeof flag === 'string' 
                          ? flag 
                          : (flag.message || flag.description || 'Payment-related issue detected')
                        }
                      </div>
                      {typeof flag === 'object' && flag.timestamp && (
                        <div className="text-xs text-red-600 flex items-center gap-1">
                          <Clock className="h-3 w-3 flex-shrink-0" />
                          <span className="break-words">{flag.timestamp}</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {paymentFlags.length > 5 && (
                  <p className="text-xs text-muted-foreground text-center pt-1">
                    +{paymentFlags.length - 5} more payment-related issues
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Summary Stats */}
          <div className="grid grid-cols-2 gap-4 pt-2 border-t text-center">
            <div>
              <div className="text-lg font-bold">
                {redFlags.length}
              </div>
              <div className="text-xs text-muted-foreground">
                Total Flags
              </div>
            </div>
            <div>
              <div className="text-lg font-bold">
                {paymentFlags.length}
              </div>
              <div className="text-xs text-muted-foreground">
                Payment Issues
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
