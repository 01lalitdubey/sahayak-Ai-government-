"use client";

import React, { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { adminTmsApi } from "@/lib/api/admin-tms";
import type { TranslationTMSDetail, TranslationHistory } from "@/lib/api/admin-tms";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { ArrowLeft, Check, X, Send } from "lucide-react";

export default function TranslationReviewPage() {
  const router = useRouter();
  const params = useParams();
  const translationId = params.id as string;
  
  const [translation, setTranslation] = useState<TranslationTMSDetail | null>(null);
  const [editedContent, setEditedContent] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [reviewComment, setReviewComment] = useState("");

  useEffect(() => {
    async function loadData() {
      try {
        const data = await adminTmsApi.getTranslation(translationId);
        setTranslation(data);
        setEditedContent(data.translated_content);
      } catch (e) {
        console.error(e);
        toast("Failed to load translation");
      } finally {
        setLoading(false);
      }
    }
    if (translationId) {
      loadData();
    }
  }, [translationId]);

  const handleSaveEdits = async () => {
    try {
      const updated = await adminTmsApi.updateTranslation(translationId, editedContent, "Manual edit by reviewer");
      setTranslation(updated);
      toast("Translation updated successfully");
    } catch (e) {
      console.error(e);
      toast("Failed to update translation");
    }
  };

  const handleApprove = async () => {
    try {
      const updated = await adminTmsApi.approveTranslation(translationId, reviewComment);
      setTranslation(updated);
      toast("Translation approved");
    } catch {
      toast("Failed to approve translation");
    }
  };

  const handleReject = async () => {
    if (!reviewComment) {
      toast("Please provide a reason for rejection");
      return;
    }
    try {
      const updated = await adminTmsApi.rejectTranslation(translationId, reviewComment);
      setTranslation(updated);
      toast("Translation rejected");
    } catch {
      toast("Failed to reject translation");
    }
  };

  const handlePublish = async () => {
    try {
      const updated = await adminTmsApi.publishTranslation(translationId);
      setTranslation(updated);
      toast("Translation published");
    } catch {
      toast("Failed to publish translation");
    }
  };

  if (loading) return <div className="container mx-auto p-8 text-center">Loading translation...</div>;
  if (!translation) return <div className="container mx-auto p-8 text-center text-red-500">Translation not found</div>;

  const contentKeys = Object.keys(translation.translated_content || {});

  return (
    <div className="container mx-auto py-8 px-4 max-w-6xl">
      <div className="flex items-center space-x-4 mb-6">
        <Button variant="ghost" onClick={() => router.push('/admin/tms')}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to list
        </Button>
        <h1 className="text-2xl font-bold flex-1 truncate">{translation.scheme_name || "Translation Review"}</h1>
        <Badge variant={translation.status === 'published' ? 'default' : 'secondary'} className="text-sm px-3 py-1">
          {translation.status.toUpperCase()}
        </Badge>
        <Badge variant="outline" className="text-sm px-3 py-1 bg-slate-100">
          v{translation.version}
        </Badge>
        <Badge variant="outline" className="text-sm px-3 py-1 uppercase font-semibold">
          {translation.language_code}
        </Badge>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {/* Editor Section */}
        <div className="md:col-span-2 space-y-6">
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle>Content Editor</CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue={contentKeys[0]}>
                <TabsList className="mb-4 flex flex-wrap h-auto gap-2">
                  {contentKeys.map((key) => (
                    <TabsTrigger key={key} value={key} className="capitalize">{key.replace('_', ' ')}</TabsTrigger>
                  ))}
                </TabsList>
                {contentKeys.map((key) => (
                  <TabsContent key={key} value={key} className="space-y-4">
                    <div className="p-4 bg-slate-50 rounded-md border text-sm text-slate-700">
                      <strong>Original English:</strong><br/>
                      {translation.original_english?.[key] || "Original content not loaded in detail API"}
                    </div>
                    <div>
                      <label className="text-sm font-medium mb-2 block">Translation:</label>
                      <Textarea 
                        className="min-h-[200px] text-base"
                        value={editedContent[key] || ""}
                        onChange={(e) => setEditedContent({...editedContent, [key]: e.target.value})}
                      />
                    </div>
                  </TabsContent>
                ))}
              </Tabs>
              
              <div className="mt-6 flex justify-end">
                <Button onClick={handleSaveEdits}>Save Edits</Button>
              </div>
            </CardContent>
          </Card>
          
          {/* History */}
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle>Revision History</CardTitle>
            </CardHeader>
            <CardContent>
              {translation.history && translation.history.length > 0 ? (
                <ul className="space-y-4">
                  {translation.history.map((h: TranslationHistory) => (
                    <li key={h.id} className="text-sm border-b pb-4 last:border-0 last:pb-0">
                      <div className="flex justify-between items-start mb-1">
                        <span className="font-semibold">Version {h.version}</span>
                        <span className="text-muted-foreground">{new Date(h.created_at).toLocaleString()}</span>
                      </div>
                      <p className="text-slate-600">Reason: {h.reason || "No reason provided"}</p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-muted-foreground text-sm">No previous revisions.</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Action Panel */}
        <div className="space-y-6">
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle>Review Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Review Comment</label>
                <Textarea 
                  placeholder="Optional context for approval, required for rejection"
                  value={reviewComment}
                  onChange={(e) => setReviewComment(e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-3 pt-2">
                {translation.status !== 'approved' && translation.status !== 'published' && (
                  <>
                    <Button variant="default" className="w-full justify-start bg-green-600 hover:bg-green-700" onClick={handleApprove}>
                      <Check className="w-4 h-4 mr-2" /> Approve Translation
                    </Button>
                    <Button variant="destructive" className="w-full justify-start" onClick={handleReject}>
                      <X className="w-4 h-4 mr-2" /> Reject
                    </Button>
                  </>
                )}
                {translation.status === 'approved' && (
                  <Button variant="default" className="w-full justify-start" onClick={handlePublish}>
                    <Send className="w-4 h-4 mr-2" /> Publish to Public
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle>Metadata</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Provider:</span>
                <span className="font-medium">{translation.provider}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Quality Score:</span>
                <span className="font-medium">{translation.translation_quality ? `${translation.translation_quality}%` : 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Created:</span>
                <span className="font-medium">{new Date(translation.created_at).toLocaleDateString()}</span>
              </div>
              {translation.published_at && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Published:</span>
                  <span className="font-medium">{new Date(translation.published_at).toLocaleDateString()}</span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
