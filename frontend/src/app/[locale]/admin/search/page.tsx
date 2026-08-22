"use client";

import React from "react";

export default function AdminSearchPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Search & Discovery</h1>
      <div className="bg-white p-6 rounded-lg shadow text-center text-gray-500 py-12 border border-dashed border-gray-300">
        <p className="mb-2">Search analytics and popular queries will be displayed here.</p>
        <p className="text-sm">Pending integration with Elasticsearch/PostgreSQL full-text search logs.</p>
      </div>
    </div>
  );
}
