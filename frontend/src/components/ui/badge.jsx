import * as React from "react"
import { cva } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-[8px] px-2.5 py-0.5 text-xs font-semibold transition-colors",
  {
    variants: {
      variant: {
        default:
          "bg-[rgba(249,115,22,0.15)] text-[#F97316] border border-[rgba(249,115,22,0.25)]",
        secondary:
          "bg-[rgba(255,255,255,0.08)] text-[#94A3B8] border border-[rgba(255,255,255,0.1)]",
        destructive:
          "bg-[rgba(239,68,68,0.15)] text-[#EF4444] border border-[rgba(239,68,68,0.25)]",
        success:
          "bg-[rgba(16,185,129,0.15)] text-[#10B981] border border-[rgba(16,185,129,0.25)]",
        warning:
          "bg-[rgba(245,158,11,0.15)] text-[#F59E0B] border border-[rgba(245,158,11,0.25)]",
        info:
          "bg-[rgba(59,130,246,0.15)] text-[#3B82F6] border border-[rgba(59,130,246,0.25)]",
        outline:
          "border border-[rgba(255,255,255,0.15)] text-[#E2E8F0]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Badge({ className, variant, ...props }) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
