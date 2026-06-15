import * as React from "react"
import { cn } from "@/lib/utils"

const Input = React.forwardRef(({ className, type, ...props }, ref) => {
  return (
    <input
      type={type}
      className={cn(
        "flex h-10 w-full rounded-[10px] border px-3 py-2 text-sm transition-all duration-200",
        "bg-[rgba(255,255,255,0.05)] border-[rgba(255,255,255,0.12)] text-[#E2E8F0]",
        "placeholder:text-[#94A3B8]",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#F97316] focus-visible:ring-offset-0 focus-visible:border-[#F97316]",
        "disabled:cursor-not-allowed disabled:opacity-50",
        "file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-[#E2E8F0]",
        className
      )}
      ref={ref}
      {...props}
    />
  )
})
Input.displayName = "Input"

export { Input }
