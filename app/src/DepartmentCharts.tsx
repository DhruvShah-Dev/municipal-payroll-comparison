import { cities, latestYear, story } from './data'
import { formatMoney, formatPercent, formatSignedMoney, shortDepartment } from './format'
import { useTooltip } from './tooltip'
import type { DepartmentYear, Driver } from './types'

function DepartmentTooltip({ row }: { row: DepartmentYear | Driver }) {
  return {
    title: shortDepartment(row.department),
    items: [
      { label: 'Overtime pay', value: formatMoney(row.overtime_pay_usd) },
      { label: 'Share of city overtime', value: formatPercent(row.share_of_city_overtime) },
      ...(row.overtime_change_usd === null ? [] : [{ label: `Change vs ${row.year - 1}`, value: formatSignedMoney(row.overtime_change_usd) }]),
      { label: 'Of department pay', value: row.overtime_share_of_department_pay === null ? 'Not available' : formatPercent(row.overtime_share_of_department_pay) },
    ],
    note: `Source period: ${row.year}`,
  }
}

export function DepartmentRankings() {
  const { show, hide } = useTooltip()
  return (
    <div className="ranking-grid">
      {cities.map((city) => {
        const rows = story.top_departments.filter((row) => row.city === city)
        const maximum = Math.max(...rows.map((row) => row.overtime_pay_usd))
        return (
          <article className="ranking" key={city}>
            <h3>{city}</h3>
            <p>Top five departments by overtime pay, {latestYear}</p>
            <ol>
              {rows.map((row) => (
                <li key={row.department}>
                  <span title={row.department}>{shortDepartment(row.department)}</span>
                  <button
                    className="ranking-mark"
                    style={{ '--bar-width': `${Math.max(10, row.overtime_pay_usd / maximum * 100)}%` } as React.CSSProperties}
                    aria-label={`${row.department}, overtime pay ${formatMoney(row.overtime_pay_usd)}`}
                    aria-describedby="data-tooltip"
                    onFocus={(event) => show(event, DepartmentTooltip({ row }))} onBlur={hide}
                    onMouseEnter={(event) => show(event, DepartmentTooltip({ row }))} onMouseMove={(event) => show(event, DepartmentTooltip({ row }))} onMouseLeave={hide}
                  ><i /><b>{formatMoney(row.overtime_pay_usd)}</b></button>
                </li>
              ))}
            </ol>
            <p className="concentration-note">Top five: {formatPercent(story.concentrations.find((row) => row.city === city)!.top_five_share)} of city overtime</p>
          </article>
        )
      })}
    </div>
  )
}

export function DriverCharts() {
  const { show, hide } = useTooltip()
  return (
    <div className="driver-grid">
      {cities.map((city) => {
        const rows = story.drivers.filter((row) => row.city === city).sort((a, b) => a.overtime_change_usd - b.overtime_change_usd)
        const maximum = Math.max(...rows.map((row) => Math.abs(row.overtime_change_usd)))
        return (
          <article className="driver-chart" key={city}>
            <h3>{city}</h3>
            <p>Largest department contributions to the {latestYear - 1}→{latestYear} change</p>
            <div className="driver-axis" aria-hidden="true"><span>Decrease</span><span>Increase</span></div>
            <ul>
              {rows.map((row) => {
                const positive = row.overtime_change_usd >= 0
                return (
                  <li key={row.department}>
                    <span title={row.department}>{shortDepartment(row.department)}</span>
                    <div className="driver-track">
                      <button
                        className={`driver-mark ${positive ? 'positive' : 'negative'}`}
                        style={{ '--driver-width': `${Math.max(2, Math.abs(row.overtime_change_usd) / maximum * 48)}%` } as React.CSSProperties}
                        aria-label={`${row.department}, change ${formatSignedMoney(row.overtime_change_usd)}`}
                        aria-describedby="data-tooltip"
                        onFocus={(event) => show(event, DepartmentTooltip({ row }))} onBlur={hide}
                        onMouseEnter={(event) => show(event, DepartmentTooltip({ row }))} onMouseMove={(event) => show(event, DepartmentTooltip({ row }))} onMouseLeave={hide}
                      />
                      <b className={positive ? 'value-positive' : 'value-negative'}>{formatSignedMoney(row.overtime_change_usd)}</b>
                    </div>
                  </li>
                )
              })}
            </ul>
          </article>
        )
      })}
    </div>
  )
}
