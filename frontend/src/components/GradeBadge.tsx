const GRADE_STYLES: Record<string, string> = {
  A: "bg-emerald-500/10 text-emerald-400 ring-emerald-500/20",
  B: "bg-blue-500/10 text-blue-400 ring-blue-500/20",
  C: "bg-amber-500/10 text-amber-400 ring-amber-500/20",
  D: "bg-orange-500/10 text-orange-400 ring-orange-500/20",
  F: "bg-red-500/10 text-red-400 ring-red-500/20",
};

export function GradeBadge({ grade, size = "md" }: { grade: string; size?: "sm" | "md" | "lg" }) {
  const sizeClass = size === "lg" ? "w-14 h-14 text-2xl" : size === "sm" ? "w-7 h-7 text-xs" : "w-9 h-9 text-sm";

  return (
    <span
      className={`inline-flex items-center justify-center rounded-lg font-bold font-mono ring-1 ring-inset ${sizeClass} ${GRADE_STYLES[grade] || GRADE_STYLES.F}`}
    >
      {grade}
    </span>
  );
}
