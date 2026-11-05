import { createContext, useCallback, useContext, useEffect, useMemo, useState, type PropsWithChildren, type SyntheticEvent } from 'react'
import type { TooltipContent } from './types'

interface TooltipState extends TooltipContent {
  x: number
  y: number
}

interface TooltipApi {
  show: (event: SyntheticEvent<Element>, content: TooltipContent) => void
  hide: () => void
}

const TooltipContext = createContext<TooltipApi | null>(null)

function pointFromEvent(event: SyntheticEvent<Element>) {
  const native = event.nativeEvent as Event & { clientX?: number; clientY?: number }
  if (typeof native.clientX === 'number' && typeof native.clientY === 'number' && native.clientX > 0) {
    return { x: native.clientX, y: native.clientY }
  }
  const rect = event.currentTarget.getBoundingClientRect()
  return { x: rect.right, y: rect.top + rect.height / 2 }
}

export function TooltipProvider({ children }: PropsWithChildren) {
  const [tooltip, setTooltip] = useState<TooltipState | null>(null)
  const show = useCallback((event: SyntheticEvent<Element>, content: TooltipContent) => {
    const point = pointFromEvent(event)
    setTooltip({ ...content, ...point })
  }, [])
  const hide = useCallback(() => setTooltip(null), [])

  useEffect(() => {
    const close = (event: KeyboardEvent) => event.key === 'Escape' && hide()
    window.addEventListener('keydown', close)
    return () => window.removeEventListener('keydown', close)
  }, [hide])

  const api = useMemo(() => ({ show, hide }), [show, hide])
  return (
    <TooltipContext.Provider value={api}>
      {children}
      {tooltip ? <DataTooltip {...tooltip} /> : null}
    </TooltipContext.Provider>
  )
}

export function useTooltip() {
  const context = useContext(TooltipContext)
  if (!context) throw new Error('useTooltip must be used within TooltipProvider')
  return context
}

function DataTooltip({ title, items, note, x, y }: TooltipState) {
  const width = Math.min(320, window.innerWidth - 24)
  const left = Math.max(12, Math.min(x + 16, window.innerWidth - width - 12))
  const top = Math.max(12, Math.min(y + 16, window.innerHeight - 230))
  return (
    <aside id="data-tooltip" className="data-tooltip" role="tooltip" style={{ left, top, width }}>
      <strong>{title}</strong>
      <dl>
        {items.map((item) => (
          <div key={item.label}>
            <dt>{item.label}</dt>
            <dd>{item.value}</dd>
          </div>
        ))}
      </dl>
      {note ? <p>{note}</p> : null}
    </aside>
  )
}
