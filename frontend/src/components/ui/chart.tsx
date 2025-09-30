import { cn } from "@/lib/utils"

interface AudioVisualizerProps {
  audioData: number[]
  isPlaying: boolean
  progress: number
  className?: string
  barCount?: number
}

export function AudioVisualizer({ 
  audioData, 
  isPlaying, 
  progress, 
  className,
  barCount = 35 
}: AudioVisualizerProps) {
  return (
    <div className={cn("h-10 flex items-end justify-center gap-1 px-2 flex-shrink-0", className)}>
      {audioData.slice(0, barCount).map((height, index) => {
        const barHeight = Math.max(4, height * 0.3)
        // Calculate fill based on progress - bars fill from left to right
        const progressPerBar = 100 / barCount
        const barStartProgress = index * progressPerBar
        const barEndProgress = (index + 1) * progressPerBar

        let fillPercentage = 0
        if (isPlaying && progress > barStartProgress) {
          if (progress >= barEndProgress) {
            fillPercentage = 100 // Fully filled
          } else {
            // Partially filled based on progress within this bar's range
            fillPercentage = ((progress - barStartProgress) / progressPerBar) * 100
          }
        }

        return (
          <div key={index} className="relative w-1">
            {/* Dark gray background bar */}
            <div
              className="bg-gray-600 w-full transition-all duration-100 rounded-t"
              style={{ height: `${barHeight}px` }}
            />
            {/* Red fill overlay */}
            <div
              className="absolute bottom-0 left-0 w-full bg-red-600 transition-all duration-300 rounded-t"
              style={{
                height: `${(barHeight * fillPercentage) / 100}px`,
              }}
            />
          </div>
        )
      })}
    </div>
  )
}