import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-[10px] text-sm font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#F97316] focus-visible:ring-offset-2 focus-visible:ring-offset-[#0B1220] disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        /* Primaire — gradient orange */
        default:
          "bg-gradient-to-r from-[#F97316] to-[#FB923C] text-white shadow-[0_4px_14px_rgba(249,115,22,0.35)] hover:brightness-110 hover:shadow-[0_6px_20px_rgba(249,115,22,0.45)] active:brightness-95",
        /* Destructive */
        destructive:
          "bg-[#EF4444] text-white shadow-sm hover:bg-[#DC2626]",
        /* Secondaire — bordure orange */
        outline:
          "border border-[rgba(255,255,255,0.15)] bg-transparent text-[#E2E8F0] hover:bg-[rgba(255,255,255,0.07)] hover:border-[rgba(255,255,255,0.25)]",
        /* Secondary */
        secondary:
          "bg-[rgba(255,255,255,0.08)] text-[#E2E8F0] hover:bg-[rgba(255,255,255,0.13)] border border-[rgba(255,255,255,0.1)]",
        /* Ghost */
        ghost:
          "bg-transparent text-[#94A3B8] hover:bg-[rgba(255,255,255,0.07)] hover:text-[#E2E8F0]",
        /* Lien */
        link:
          "text-[#F97316] underline-offset-4 hover:underline bg-transparent",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm:      "h-8 px-3 text-xs rounded-[8px]",
        lg:      "h-11 px-6 rounded-[12px] text-base",
        xl:      "h-12 px-8 rounded-[12px] text-base",
        icon:    "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

const Button = React.forwardRef(({ className, variant, size, asChild = false, ...props }, ref) => {
  const Comp = asChild ? Slot : "button"
  return (
    <Comp
      className={cn(buttonVariants({ variant, size, className }))}
      ref={ref}
      {...props}
    />
  )
})
Button.displayName = "Button"

export { Button, buttonVariants }
