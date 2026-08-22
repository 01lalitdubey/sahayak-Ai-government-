"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";
import { 
  LayoutDashboard, 
  Users, 
  FileText, 
  Languages, 
  Brain, 
  Search, 
  BarChart, 
  FileBox, 
  Activity, 
  Settings,
  Menu,
  X
} from "lucide-react";

export function AdminSidebar() {
  const t = useTranslations("admin");
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);

  const getLocalePrefix = () => {
    const parts = pathname.split("/");
    return parts.length > 1 ? `/${parts[1]}` : "/en";
  };
  const localePrefix = getLocalePrefix();

  const links = [
    { href: `${localePrefix}/admin`, label: t("overview"), icon: LayoutDashboard },
    { href: `${localePrefix}/admin/users`, label: t("users"), icon: Users },
    { href: `${localePrefix}/admin/schemes`, label: t("schemes"), icon: FileText },
    { href: `${localePrefix}/admin/translations`, label: t("translations"), icon: Languages },
    { href: `${localePrefix}/admin/ai`, label: t("ai"), icon: Brain },
    { href: `${localePrefix}/admin/search`, label: t("search_discovery"), icon: Search },
    { href: `${localePrefix}/admin/analytics`, label: t("analytics"), icon: BarChart },
    { href: `${localePrefix}/admin/content`, label: t("content"), icon: FileBox },
    { href: `${localePrefix}/admin/system`, label: t("system"), icon: Activity },
    { href: `${localePrefix}/admin/settings`, label: t("settings"), icon: Settings },
  ];

  return (
    <>
      {/* Mobile Toggle */}
      <button 
        className="md:hidden fixed top-4 left-4 z-50 p-2 bg-white rounded-md shadow-md text-gray-600"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* Backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside 
        className={`fixed md:sticky top-0 left-0 h-screen w-64 bg-white border-r border-gray-200 z-50 transform transition-transform duration-200 ease-in-out flex flex-col ${
          isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
      >
        <div className="h-16 flex items-center px-6 border-b border-gray-200">
          <Link href="/" className="font-bold text-xl text-primary-600">
            Sahayak AI
          </Link>
          <span className="ml-2 text-xs font-semibold px-2 py-1 bg-gray-100 text-gray-600 rounded-md">Admin</span>
        </div>

        <div className="flex-1 overflow-y-auto py-4">
          <nav className="space-y-1 px-3">
            {links.map((link) => {
              const isActive = pathname === link.href || (link.href !== `${localePrefix}/admin` && pathname.startsWith(link.href));
              const Icon = link.icon;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setIsOpen(false)}
                  className={`flex items-center px-3 py-2.5 text-sm font-medium rounded-md transition-colors ${
                    isActive
                      ? "bg-primary-50 text-primary-700"
                      : "text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                  }`}
                >
                  <Icon className={`mr-3 h-5 w-5 flex-shrink-0 ${isActive ? "text-primary-700" : "text-gray-400"}`} />
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </aside>
    </>
  );
}
