"use client";

import { useState } from "react";
import { logger } from "@/lib/logger";
import { useLocale } from "next-intl";
import { ThumbsUp, ThumbsDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import api from "@/lib/axios";
import { toast } from "sonner";
import { Card, CardContent } from "@/components/ui/card";

interface TranslationFeedbackProps {
  schemeId: string;
}

export function TranslationFeedback({ schemeId }: TranslationFeedbackProps) {
  const locale = useLocale();
  const [isHelpful, setIsHelpful] = useState<boolean | null>(null);
  const [comment, setComment] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  // If locale is english, no translation feedback is needed.
  if (locale === "en") return null;

  const handleSubmit = async () => {
    if (isHelpful === null) return;
    
    setLoading(true);
    try {
      await api.post(`/schemes/${schemeId}/feedback`, {
        is_helpful: isHelpful,
        comment: comment,
      }, {
        headers: {
          'Accept-Language': locale
        }
      });
      setSubmitted(true);
      toast("Thank you for your feedback!");
    } catch (e) {
      logger.error(e);
      toast("Failed to submit feedback. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <Card className="bg-slate-50 border-none shadow-none mt-6">
        <CardContent className="p-6 text-center text-sm text-muted-foreground">
          Thank you for helping us improve our translations!
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-slate-50 border border-slate-100 shadow-sm mt-8">
      <CardContent className="p-6">
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-slate-800">Was this translation helpful?</h3>
          
          <div className="flex gap-2">
            <Button 
              variant={isHelpful === true ? "default" : "outline"} 
              size="sm"
              onClick={() => setIsHelpful(true)}
              className="gap-2"
            >
              <ThumbsUp className="w-4 h-4" /> Yes
            </Button>
            <Button 
              variant={isHelpful === false ? "destructive" : "outline"} 
              size="sm"
              onClick={() => setIsHelpful(false)}
              className="gap-2"
            >
              <ThumbsDown className="w-4 h-4" /> No
            </Button>
          </div>

          {isHelpful !== null && (
            <div className="space-y-3 pt-2">
              <Textarea 
                placeholder="Tell us what could be improved..."
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                className="text-sm"
              />
              <Button onClick={handleSubmit} disabled={loading} size="sm">
                Submit Feedback
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
