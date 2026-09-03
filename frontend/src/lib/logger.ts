/**
 * logger — Sahayak AI frontend
 * Thin wrapper over `console` so call sites don't reference it directly.
 * `error` / `warn` always emit (they matter in production too);
 * `debug` / `info` are silenced outside development.
 */

const isDev = process.env.NODE_ENV !== "production";

/* eslint-disable no-console -- this module is the sanctioned console wrapper */
export const logger = {
  debug: (...args: unknown[]) => {
    if (isDev) console.debug(...args);
  },
  info: (...args: unknown[]) => {
    if (isDev) console.info(...args);
  },
  warn: (...args: unknown[]) => {
    console.warn(...args);
  },
  error: (...args: unknown[]) => {
    console.error(...args);
  },
};
