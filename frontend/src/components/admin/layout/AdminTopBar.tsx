"use client";

import React from "react";
import { useTranslations } from "next-intl";
import { Bell, Search } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";

export function AdminTopBar() {
  const t = useTranslations("admin");
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between bg-white px-4 border-b border-gray-200 sm:px-6">
      <div className="flex items-center flex-1 md:pl-0 pl-12">
        <div className="relative w-full max-w-md hidden md:block">
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
            <Search className="h-4 w-4 text-gray-400" />
          </div>
          <input
            type="text"
            className="block w-full rounded-md border-0 py-1.5 pl-10 pr-3 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-primary-600 sm:text-sm sm:leading-6"
            placeholder={t("search")}
          />
        </div>
      </div>
      
      <div className="flex items-center space-x-4">
        <button className="text-gray-500 hover:text-gray-700 relative">
          <Bell className="h-5 w-5" />
          <span className="absolute top-0 right-0 block h-2 w-2 rounded-full bg-red-400 ring-2 ring-white" />
        </button>

        <div className="flex items-center space-x-3 pl-4 border-l border-gray-200">
          <div className="flex flex-col text-right hidden sm:block">
            <span className="text-sm font-medium text-gray-900">{user?.full_name || "Admin"}</span>
            <span className="text-xs text-gray-500">{user?.role || "Admin"}</span>
          </div>
          <button onClick={() => logout()} className="text-sm font-medium text-primary-600 hover:text-primary-700">
            {t("logout")}
          </button>
        </div>
      </div>
    </header>
  );
}
