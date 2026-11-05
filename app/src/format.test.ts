import { describe, expect, it } from 'vitest'
import { formatMoney, formatPercentagePoints, formatPercent, formatSignedMoney, shortDepartment } from './format'

describe('formatters', () => {
  it('formats report units consistently', () => {
    expect(formatPercent(0.1069446)).toBe('10.7%')
    expect(formatPercentagePoints(-1.6944)).toBe('−1.69 pp')
    expect(formatMoney(469_896_049)).toBe('$469.9M')
    expect(formatSignedMoney(-35_896_744)).toBe('−$35.9M')
  })

  it('shortens published department prefixes without changing identity', () => {
    expect(shortDepartment('D57 - Chicago Police Department')).toBe('Chicago Police')
    expect(shortDepartment('DEPARTMENT OF SANITATION')).toBe('SANITATION')
  })
})
