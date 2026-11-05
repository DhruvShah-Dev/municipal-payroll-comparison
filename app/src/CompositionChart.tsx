import { latestCityRows } from './data'
import { formatMoney, formatPercent } from './format'
import { useTooltip } from './tooltip'

const components = [
  { key: 'regular_pay_usd', label: 'Regular pay', className: 'regular' },
  { key: 'overtime_pay_usd', label: 'Overtime', className: 'overtime' },
  { key: 'other_pay_usd', label: 'Other pay', className: 'other' },
] as const

export function CompositionChart() {
  const { show, hide } = useTooltip()
  return (
    <div className="composition-chart">
      {latestCityRows.map((row) => (
        <div className="composition-row" key={row.city}>
          <strong>{row.city}</strong>
          <div className="stacked-bar" aria-label={`${row.city} reported pay composition`}>
            {components.map((component) => {
              const amount = row[component.key]
              const share = amount / row.total_pay_usd
              const content = {
                title: `${row.city} · ${row.year}`,
                items: [
                  { label: component.label, value: formatPercent(share) },
                  { label: 'Amount', value: formatMoney(amount) },
                ],
                note: row.basis,
              }
              return (
                <button
                  key={component.key}
                  className={`stacked-segment ${component.className}`}
                  style={{ width: `${share * 100}%` }}
                  aria-label={`${row.city}, ${component.label}, ${formatPercent(share)}, ${formatMoney(amount)}`}
                  aria-describedby="data-tooltip"
                  onFocus={(event) => show(event, content)} onBlur={hide}
                  onMouseEnter={(event) => show(event, content)} onMouseMove={(event) => show(event, content)} onMouseLeave={hide}
                >
                  {component.key === 'overtime_pay_usd' ? <span>{formatPercent(share)}</span> : null}
                </button>
              )
            })}
          </div>
        </div>
      ))}
      <div className="composition-key" aria-hidden="true"><span className="key-regular">Regular</span><span className="key-overtime">Overtime</span><span className="key-other">Other</span></div>
    </div>
  )
}
