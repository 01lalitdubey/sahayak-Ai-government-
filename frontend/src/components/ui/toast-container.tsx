"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, XCircle, Info, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface Toast { id: number; message: string; type: "success" | "error" | "info"; }

export function ToastContainer() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    const handler = (e: Event) => {
      const { message, type } = (e as CustomEvent).detail;
      const id = Date.now();
      setToasts((p) => [...p, { id, message, type }]);
      setTimeout(() => setToasts((p) => p.filter((t) => t.id !== id)), 4000);
    };
    window.addEventListener("sahayak-toast", handler);
    return () => window.removeEventListener("sahayak-toast", handler);
  }, []);

  const icons = { success: CheckCircle2, error: XCircle, info: Info };
  const colours = {
    success: "bg-green-50 border-green-200 text-green-800 dark:bg-green-900/30 dark:text-green-300",
    error: "bg-red-50 border-red-200 text-red-800 dark:bg-red-900/30 dark:text-red-300",
    info: "bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  };

  return (
    <div className="fixed bottom-4 right-4 z-[9999] flex flex-col gap-2 w-80">
      <AnimatePresence>
        {toasts.map((t) => {
          const Icon = icons[t.type];
          return (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 40 }}
              className={cn("flex items-start gap-3 rounded-lg border px-4 py-3 shadow-md text-sm", colours[t.type])}
            >
              <Icon className="h-4 w-4 mt-0.5 shrink-0" />
              <span className="flex-1">{t.message}</span>
              <button onClick={() => setToasts((p) => p.filter((x) => x.id !== t.id))}>
                <X className="h-3.5 w-3.5 opacity-60 hover:opacity-100" />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
