"use client";

import React from "react";

export default function AdminAIPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">AI Dashboard</h1>
      <div className="bg-white p-6 rounded-lg shadow text-center text-gray-500 py-12 border border-dashed border-gray-300">
        <p className="mb-2">AI metrics integration is pending backend support.</p>
        <p className="text-sm">Once the AI job queues are exposed, this page will display recommendation, eligibility, and translation AI statistics.</p>
      </div>
    </div>
  );
}
