"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { apiService as api } from "@/services/api.service";
import { Activity, Database, Server } from "lucide-react";

interface SystemHealth {
  status: string;
  database: string;
  version: string;
}

export default function AdminSystemPage() {
  const { data: health, isLoading } = useQuery<SystemHealth | null>({
    queryKey: ["admin", "system", "health"],
    queryFn: async () => {
      const res = await api.get<SystemHealth>("/admin/system/health");
      return res.data;
    },
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">System Health</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-6 rounded-lg shadow flex items-center">
          <div className={`p-3 rounded-full ${health?.status === 'Healthy' ? 'bg-green-100' : 'bg-yellow-100'}`}>
            <Activity className={health?.status === 'Healthy' ? 'text-green-600' : 'text-yellow-600'} />
          </div>
          <div className="ml-4">
            <p className="text-sm text-gray-500 font-medium">Overall Status</p>
            <p className="text-xl font-bold text-gray-900">{isLoading ? "Checking..." : health?.status || "Unknown"}</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow flex items-center">
          <div className={`p-3 rounded-full ${health?.database === 'Healthy' ? 'bg-green-100' : 'bg-red-100'}`}>
            <Database className={health?.database === 'Healthy' ? 'text-green-600' : 'text-red-600'} />
          </div>
          <div className="ml-4">
            <p className="text-sm text-gray-500 font-medium">Database</p>
            <p className="text-xl font-bold text-gray-900">{isLoading ? "Checking..." : health?.database || "Unknown"}</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow flex items-center">
          <div className="p-3 rounded-full bg-blue-100">
            <Server className="text-blue-600" />
          </div>
          <div className="ml-4">
            <p className="text-sm text-gray-500 font-medium">API Version</p>
            <p className="text-xl font-bold text-gray-900">{isLoading ? "Checking..." : health?.version || "Unknown"}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
