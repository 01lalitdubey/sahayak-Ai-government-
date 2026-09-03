"use client";

import React, { useEffect, useState } from "react";
import { logger } from "@/lib/logger";
import { adminTmsApi } from "@/lib/api/admin-tms";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Play, Pause, Square, RotateCcw, AlertTriangle, Activity, Download } from "lucide-react";
import { useRouter } from "next/navigation";

interface ProgressData {
  job_id?: string;
  status?: string;
  total_records?: number;
  processed_records?: number;
  failed_records?: number;
  speed?: number;
  eta_seconds?: number;
  active_workers?: number;
  queue_size?: number;
  current_languages?: string[];
}

interface HealthData {
  recent_errors?: { scheme_id: string; language: string; error: string; timestamp: number }[];
}

export default function TranslationExecutionDashboard() {
  const router = useRouter();
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [health, setHealth] = useState<HealthData | null>(null);
  
  const fetchProgress = async () => {
    try {
      const p = await adminTmsApi.getProgress();
      setProgress(p as ProgressData);
    } catch {
      logger.error("Failed to load progress");
    }
  };

  const fetchHealth = async () => {
    try {
      const h = await adminTmsApi.getHealth();
      setHealth(h as HealthData);
    } catch {
      logger.error("Failed to load health");
    }
  };

  useEffect(() => {
    fetchProgress();
    fetchHealth();
    const interval = setInterval(() => {
      fetchProgress();
      // Fetch health less frequently if preferred, but for now we do both
      fetchHealth();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleStartAll = async () => {
    try {
      await adminTmsApi.startAll();
      toast.success("Translation execution started!");
      fetchProgress();
    } catch (e: unknown) {
      toast.error((e as { response?: { data?: { detail?: string } } }).response?.data?.detail || "Failed to start");
    }
  };

  const handlePause = async () => {
    try {
      await adminTmsApi.pauseExecution();
      toast.info("Execution paused");
      fetchProgress();
    } catch {
      toast.error("Failed to pause");
    }
  };

  const handleResume = async () => {
    try {
      await adminTmsApi.resumeExecution();
      toast.success("Execution resumed");
      fetchProgress();
    } catch {
      toast.error("Failed to resume");
    }
  };

  const handleCancel = async () => {
    if (!confirm("Are you sure you want to cancel the job?")) return;
    try {
      await adminTmsApi.cancelExecution();
      toast.warning("Execution cancelled");
      fetchProgress();
    } catch {
      toast.error("Failed to cancel");
    }
  };

  const handleRetry = async () => {
    if (!progress?.job_id) return;
    try {
      await adminTmsApi.retryFailed(progress.job_id);
      toast.success("Retrying failed items...");
      fetchProgress();
    } catch (e: unknown) {
      toast.error((e as { response?: { data?: { detail?: string } } }).response?.data?.detail || "Failed to retry");
    }
  };

  const handleExport = () => {
    window.location.href = "/api/v1/admin/tms/execution/report";
  };

  const formatETA = (seconds: number) => {
    if (seconds <= 0) return "0s";
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return `${h}h ${m}m`;
  };

  const percentComplete = progress && (progress.total_records ?? 0) > 0 
    ? Math.min(100, Math.round((((progress.processed_records ?? 0) + (progress.failed_records ?? 0)) / (progress.total_records ?? 1)) * 100))
    : 0;

  return (
    <div className="container mx-auto py-8 px-4 space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Translation Execution Monitor</h1>
          <p className="text-muted-foreground mt-1">Manage and monitor the bulk translation pipeline in real-time.</p>
        </div>
        <div className="space-x-3">
          <Button variant="outline" onClick={() => router.push('/admin/tms')}>
            Back to TMS
          </Button>
          <Button variant="outline" onClick={handleExport} className="gap-2">
            <Download className="w-4 h-4" /> Export Report
          </Button>
        </div>
      </div>

      {/* Control Panel */}
      <Card className="border-2 border-slate-200 shadow-sm">
        <CardHeader className="bg-slate-50 border-b pb-4">
          <CardTitle className="flex justify-between items-center text-lg">
            <span className="flex items-center gap-2"><Activity className="w-5 h-5 text-blue-600" /> Pipeline Controls</span>
            {progress?.status && (
              <Badge variant={progress.status === 'running' ? 'default' : progress.status === 'failed' ? 'destructive' : 'secondary'} className="uppercase">
                {progress.status}
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4 items-center">
            {progress?.status === 'running' ? (
              <Button size="lg" variant="secondary" onClick={handlePause} className="gap-2 w-32">
                <Pause className="w-5 h-5" /> Pause
              </Button>
            ) : progress?.status === 'paused' ? (
              <Button size="lg" onClick={handleResume} className="gap-2 w-32 bg-green-600 hover:bg-green-700">
                <Play className="w-5 h-5" /> Resume
              </Button>
            ) : (
              <Button size="lg" onClick={handleStartAll} className="gap-2 w-32 bg-blue-600 hover:bg-blue-700">
                <Play className="w-5 h-5" /> Start All
              </Button>
            )}
            
            <Button size="lg" variant="destructive" onClick={handleCancel} disabled={!progress || ['completed', 'cancelled'].includes(progress.status || '')} className="gap-2">
              <Square className="w-5 h-5" /> Cancel
            </Button>

            <Button size="lg" variant="outline" onClick={handleRetry} disabled={!progress?.failed_records} className="gap-2 ml-auto">
              <RotateCcw className="w-5 h-5" /> Retry Failed
            </Button>
          </div>

            <div className="mt-8 space-y-3">
              <div className="flex justify-between text-sm font-medium">
                <span>Overall Progress</span>
                <span>{percentComplete}%</span>
              </div>
              <div className="h-3 w-full bg-slate-200 rounded-full overflow-hidden">
                <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${percentComplete}%` }} />
              </div>
            <div className="flex justify-between text-xs text-muted-foreground pt-1">
              <span>{progress?.processed_records || 0} Processed</span>
              <span>{progress?.total_records || 0} Total Records</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Metrics Grid */}
      <div className="grid md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Speed</CardTitle></CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{progress?.speed ? progress.speed.toFixed(2) : '0.00'} <span className="text-sm font-normal text-muted-foreground">req/s</span></div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Estimated Time</CardTitle></CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatETA(progress?.eta_seconds || 0)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Active Workers</CardTitle></CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{progress?.active_workers || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Queue Size</CardTitle></CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{progress?.queue_size || 0}</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid md:grid-cols-2 gap-8">
        {/* Languages in Progress */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Languages In Progress</CardTitle>
          </CardHeader>
          <CardContent>
            {(progress?.current_languages?.length ?? 0) > 0 ? (
              <div className="flex flex-wrap gap-2">
                {progress?.current_languages?.map((l: string) => (
                  <Badge key={l} variant="outline" className="text-sm uppercase px-3 py-1 bg-blue-50">{l}</Badge>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground text-sm">No languages currently processing.</p>
            )}
          </CardContent>
        </Card>

        {/* Health / Errors */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2"><AlertTriangle className="w-5 h-5 text-amber-500" /> Recent Errors</CardTitle>
          </CardHeader>
          <CardContent>
            {(health?.recent_errors?.length ?? 0) > 0 ? (
              <ul className="space-y-3">
                {health?.recent_errors?.slice().reverse().map((e: { scheme_id: string; language: string; error: string; timestamp: number }, i: number) => (
                  <li key={i} className="text-xs border-b pb-2 last:border-0 bg-red-50/50 p-2 rounded">
                    <div className="font-semibold text-red-700">Scheme {e.scheme_id} ({e.language})</div>
                    <div className="text-slate-600 truncate">{e.error}</div>
                    <div className="text-muted-foreground mt-1">{new Date(e.timestamp * 1000).toLocaleTimeString()}</div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-muted-foreground text-sm">No recent errors. Pipeline is healthy.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
