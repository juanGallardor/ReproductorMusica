import * as React from "react"
import * as SliderPrimitive from "@radix-ui/react-slider"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const sliderVariants = cva(
  "relative flex w-full touch-none select-none items-center",
  {
    variants: {
      variant: {
        default: "[&>span:first-child]:bg-secondary [&>span:first-child>span]:bg-primary",
        vinyl: "[&>span:first-child]:bg-gray-800 [&>span:first-child>span]:bg-red-600",
        accent: "[&>span:first-child]:bg-muted [&>span:first-child>span]:bg-accent",
        destructive: "[&>span:first-child]:bg-secondary [&>span:first-child>span]:bg-destructive",
      },
      size: {
        default: "[&>span:first-child]:h-1.5",
        sm: "[&>span:first-child]:h-1",
        lg: "[&>span:first-child]:h-2",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

const sliderThumbVariants = cva(
  "block rounded-full border-2 bg-background shadow transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "border-primary",
        vinyl: "border-red-600",
        accent: "border-accent",
        destructive: "border-destructive",
      },
      size: {
        default: "h-4 w-4",
        sm: "h-3 w-3",
        lg: "h-5 w-5",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface SliderProps
  extends React.ComponentPropsWithoutRef<typeof SliderPrimitive.Root>,
    VariantProps<typeof sliderVariants> {}

const Slider = React.forwardRef<
  React.ElementRef<typeof SliderPrimitive.Root>,
  SliderProps
>(({ className, variant, size, ...props }, ref) => (
  <SliderPrimitive.Root
    ref={ref}
    className={cn(sliderVariants({ variant, size, className }))}
    {...props}
  >
    <SliderPrimitive.Track className="relative w-full grow overflow-hidden rounded-full">
      <SliderPrimitive.Range className="absolute h-full" />
    </SliderPrimitive.Track>
    <SliderPrimitive.Thumb className={cn(sliderThumbVariants({ variant, size }))} />
  </SliderPrimitive.Root>
))
Slider.displayName = SliderPrimitive.Root.displayName

export { Slider, sliderVariants, sliderThumbVariants }