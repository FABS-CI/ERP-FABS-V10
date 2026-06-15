import * as React from "react"

import { cn } from "@/lib/utils"

const Textarea = React.forwardRef(({ className, ...props }, ref) => {
  return (
    <textarea
      className={cn(
        "flex min-h-[80px] w-full rounded-md border border-white/10 bg-[#0B1220] px-3 py-2 text-sm text-[#E2E8F0] shadow-sm placeholder:text-[#64748B] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#F97316] focus-visible:border-[#F97316] disabled:cursor-not-allowed disabled:opacity-50 resize-y transition-colors",
        className
      )}
      ref={ref}
      {...props} />
  );
})
Textarea.displayName = "Textarea"

export { Textarea }
