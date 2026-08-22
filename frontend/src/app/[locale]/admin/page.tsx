"use client";

import React from "react";
import { useTranslations } from "next-intl";
import { useQuery } from "@tanstack/react-query";
import { Users, FileText, Languages } from "lucide-react";
import { apiService as api } from "@/services/api.service";

interface OverviewData {
  total_users: number;
  active_users: number;
  total_schemes: number;
  active_schemes: number;
  translation_records: number;
  supported_languages: number;
}

export default function AdminPage() {
  const t = useTranslations("admin");

  const { data, isLoading, error } = useQuery<OverviewData | null>({
    queryKey: ["admin", "overview"],
    queryFn: async () => {
      const res = await api.get<OverviewData>("/admin/overview");
      return res.data;
    },
  });

  if (isLoading) {
    return <div className="p-8 text-center text-gray-500">Loading overview data...</div>;
  }

  if (error) {
    return <div className="p-8 text-center text-red-500">Failed to load overview data.</div>;
  }

  const stats = [
    { name: "Total Users", value: data?.total_users || 0, icon: Users, color: "bg-blue-500" },
    { name: "Active Users", value: data?.active_users || 0, icon: Users, color: "bg-blue-600" },
    { name: "Total Schemes", value: data?.total_schemes || 0, icon: FileText, color: "bg-green-500" },
    { name: "Active Schemes", value: data?.active_schemes || 0, icon: FileText, color: "bg-green-600" },
    { name: "Translation Records", value: data?.translation_records || 0, icon: Languages, color: "bg-purple-500" },
    { name: "Supported Languages", value: data?.supported_languages || 13, icon: Languages, color: "bg-purple-600" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{t("overview")}</h1>
        <p className="mt-1 text-sm text-gray-500">
          Monitor your platform&apos;s key performance indicators and system status.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {stats.map((stat) => (
          <div key={stat.name} className="overflow-hidden rounded-lg bg-white shadow">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className={`flex h-12 w-12 items-center justify-center rounded-md ${stat.color}`}>
                    <stat.icon className="h-6 w-6 text-white" aria-hidden="true" />
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="truncate text-sm font-medium text-gray-500">{stat.name}</dt>
                    <dd>
                      <div className="text-2xl font-medium text-gray-900">{stat.value}</div>
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">Recent Activity</h3>
        <p className="text-sm text-gray-500">Activity logging system is being integrated. Check back soon for real-time audit trails.</p>
      </div>
    </div>
  );
}
