import '@testing-library/jest-dom/vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { CompositionChart } from './CompositionChart'
import { TooltipProvider } from './tooltip'

describe('composition tooltips', () => {
  it('shows share and dollars once on keyboard focus', () => {
    render(<TooltipProvider><CompositionChart /></TooltipProvider>)
    const overtime = screen.getByRole('button', { name: /Chicago, Overtime/ })
    fireEvent.focus(overtime)
    const tooltip = screen.getByRole('tooltip')
    expect(tooltip).toHaveTextContent('Chicago · 2025')
    expect(tooltip).toHaveTextContent('Overtime10.7%')
    expect(tooltip).toHaveTextContent('Amount$469.9M')
    expect(tooltip.textContent?.match(/10\.7%/g)).toHaveLength(1)
  })
})
