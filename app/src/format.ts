export const formatPercent = (value: number, digits = 1) =>
  new Intl.NumberFormat('en-US', { style: 'percent', minimumFractionDigits: digits, maximumFractionDigits: digits }).format(value)

export const formatPercentagePoints = (value: number) => `${value < 0 ? '−' : value > 0 ? '+' : ''}${Math.abs(value).toFixed(2)} pp`

export const formatMoney = (value: number, digits = 1) => {
  const absolute = Math.abs(value)
  const sign = value < 0 ? '−' : value > 0 ? '' : ''
  if (absolute >= 1_000_000_000) return `${sign}$${(absolute / 1_000_000_000).toFixed(digits)}B`
  if (absolute >= 1_000_000) return `${sign}$${(absolute / 1_000_000).toFixed(digits)}M`
  if (absolute >= 1_000) return `${sign}$${(absolute / 1_000).toFixed(digits)}k`
  return `${sign}$${absolute.toFixed(0)}`
}

export const formatSignedMoney = (value: number) => `${value > 0 ? '+' : ''}${formatMoney(value)}`

export const shortDepartment = (value: string) => value
  .replace(/^D\d+\s+-\s+/, '')
  .replace('DEPARTMENT OF ', '')
  .replace('DEPT OF ', '')
  .replace('NYC ', '')
  .replace(/\bDepartment\b/g, '')
  .replace(/\s{2,}/g, ' ')
  .trim()
