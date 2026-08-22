"use client";

import React, { useEffect, useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { adminTmsApi } from "@/lib/api/admin-tms";
import type { TranslationTMSDetail } from "@/lib/api/admin-tms";
import { useRouter } from "next/navigation";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner"; // assuming sonner is used, if not we can use generic alert

export function TranslationTable() {
  const [translations, setTranslations] = useState<TranslationTMSDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const router = useRouter();

  const loadTranslations = async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page: 1, size: 50 };
      if (statusFilter !== "all") {
        params.status = statusFilter;
      }
      const data = await adminTmsApi.getTranslations(params);
      setTranslations(data.items);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTranslations();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter]);

  const toggleSelect = (id: string) => {
    const next = new Set(selectedIds);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    setSelectedIds(next);
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === translations.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(translations.map((t) => t.id)));
    }
  };

  const handleBulkApprove = async () => {
    if (selectedIds.size === 0) return;
    try {
      await adminTmsApi.bulkApprove(Array.from(selectedIds));
      toast("Translations approved successfully");
      setSelectedIds(new Set());
      loadTranslations();
    } catch (e) {
      console.error(e);
      toast("Failed to approve translations");
    }
  };

  const handleBulkPublish = async () => {
    if (selectedIds.size === 0) return;
    try {
      await adminTmsApi.bulkPublish(Array.from(selectedIds));
      toast("Translations published successfully");
      setSelectedIds(new Set());
      loadTranslations();
    } catch (e) {
      console.error(e);
      toast("Failed to publish translations");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center bg-white p-4 rounded-lg border shadow-sm">
        <div className="flex items-center space-x-4">
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="pending_review">Pending Review</SelectItem>
              <SelectItem value="approved">Approved</SelectItem>
              <SelectItem value="published">Published</SelectItem>
              <SelectItem value="rejected">Rejected</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={() => router.push('/admin/tms/execution')} className="mr-4">
            Pipeline Execution Monitor
          </Button>
          <Button variant="outline" onClick={handleBulkApprove} disabled={selectedIds.size === 0}>
            Approve Selected
          </Button>
          <Button onClick={handleBulkPublish} disabled={selectedIds.size === 0}>
            Publish Selected
          </Button>
        </div>
      </div>

      <div className="rounded-md border bg-white shadow-sm overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-slate-50">
              <TableHead className="w-[50px]">
                <Checkbox 
                  checked={translations.length > 0 && selectedIds.size === translations.length}
                  onCheckedChange={toggleSelectAll}
                />
              </TableHead>
              <TableHead>Scheme</TableHead>
              <TableHead>Language</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Quality</TableHead>
              <TableHead>Last Updated</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                  Loading translations...
                </TableCell>
              </TableRow>
            ) : translations.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                  No translations found.
                </TableCell>
              </TableRow>
            ) : (
              translations.map((t) => (
                <TableRow key={t.id} className="hover:bg-slate-50 transition-colors">
                  <TableCell>
                    <Checkbox 
                      checked={selectedIds.has(t.id)}
                      onCheckedChange={() => toggleSelect(t.id)}
                    />
                  </TableCell>
                  <TableCell className="font-medium truncate max-w-[200px]" title={t.scheme_name}>
                    {t.scheme_name || t.scheme_id}
                  </TableCell>
                  <TableCell>
                    <Badge variant="secondary" className="uppercase font-semibold tracking-wider">
                      {t.language_code}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge 
                      variant={
                        t.status === 'published' ? 'default' :
                        t.status === 'approved' ? 'outline' :
                        t.status === 'rejected' ? 'destructive' :
                        'secondary'
                      }
                      className="capitalize font-semibold"
                    >
                      {t.status.replace('_', ' ')}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {t.translation_quality ? (
                      <span className="text-sm text-slate-600 font-medium">{t.translation_quality}%</span>
                    ) : (
                      <span className="text-sm text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell className="text-sm text-slate-600">
                    {new Date(t.updated_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button 
                      variant="ghost" 
                      size="sm"
                      className="hover:bg-blue-50 hover:text-blue-600"
                      onClick={() => router.push(`/admin/tms/${t.id}`)}
                    >
                      Review
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
