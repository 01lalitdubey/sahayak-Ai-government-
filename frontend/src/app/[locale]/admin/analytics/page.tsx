"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import apiClient from "@/lib/axios";

interface GrowthResponse {
  data: number[];
  labels: string[];
}

export default function AdminAnalyticsPage() {
  const { data: growth, isLoading: growthLoading } = useQuery<GrowthResponse>({
    queryKey: ["admin", "analytics", "growth"],
    queryFn: async () => {
      const res = await apiClient.get<GrowthResponse>("/admin/analytics/growth");
      return res.data;
    },
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">User Growth (Last 7 Days)</h3>
          {growthLoading ? (
            <div className="h-48 flex items-center justify-center text-gray-500">Loading chart data...</div>
          ) : (
            <div className="h-48 flex items-end space-x-2">
              {growth?.data?.map((val: number, i: number) => (
                <div key={i} className="flex flex-col items-center flex-1">
                  <div 
                    className="w-full bg-blue-500 rounded-t" 
                    style={{ height: `${(val / Math.max(...growth.data)) * 100}%` }}
                  />
                  <span className="text-xs text-gray-500 mt-2">{growth.labels[i]}</span>
                </div>
              ))}
            </div>
          )}
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Scheme Analytics</h3>
          <div className="h-48 flex items-center justify-center text-gray-500 bg-gray-50 rounded border border-dashed border-gray-300">
            Charts component will be integrated here
          </div>
        </div>
      </div>
    </div>
  );
}
