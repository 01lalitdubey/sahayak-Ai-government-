import { Badge } from "@/components/ui/badge";
import { Star } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTranslations } from "next-intl";

export function SchemeStatusBadge({ isActive }: { isActive: boolean }) {
  const t = useTranslations("schemes");
  return (
    <Badge variant={isActive ? "default" : "secondary"} className={cn(!isActive && "opacity-60")}>
      {isActive ? t("active") : t("inactive")}
    </Badge>
  );
}

export function SchemeCategoryBadge({ category }: { category: string | null }) {
  if (!category) return null;
  return (
    <Badge variant="outline" className="text-xs capitalize">
      {category.replace(/_/g, " ")}
    </Badge>
  );
}

export function SchemeTypeBadge({ type }: { type: string }) {
  const t = useTranslations("schemes");
  return (
    <Badge
      className={cn(
        "text-xs",
        type === "central"
          ? "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 border-blue-200"
          : "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300 border-orange-200",
      )}
      variant="outline"
    >
      {type === "central" ? t("central") : t("state")}
    </Badge>
  );
}

export function FeaturedBadge() {
  const t = useTranslations("schemes");
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300">
      <Star className="h-3 w-3 fill-current" />
      {t("featured")}
    </span>
  );
}
