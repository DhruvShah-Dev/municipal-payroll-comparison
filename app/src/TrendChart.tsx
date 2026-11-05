import { CartesianGrid, Line, LineChart, ResponsiveContainer, XAxis, YAxis } from 'recharts'
import { cities, cityColor, story } from './data'
import { formatMoney, formatPercentagePoints, formatPercent } from './format'
import { useTooltip } from './tooltip'
import type { CityYear } from './types'

interface DotProps {
  cx?: number
  cy?: number
  payload?: CityYear
}

function TrendDot({ cx = 0, cy = 0, payload }: DotProps) {
  const { show, hide } = useTooltip()
  if (!payload) return null
  const latest = payload.year === story.metadata.latest_complete_year
  const tooltip = {
    title: `${payload.city} · ${payload.basis.replace(/\s*\(.+\)/, '')} ${payload.year}`,
    items: [
      { label: 'Overtime share', value: formatPercent(payload.overtime_share) },
      { label: 'Overtime pay', value: formatMoney(payload.overtime_pay_usd) },
      { label: 'Total reported pay', value: formatMoney(payload.total_pay_usd) },
      ...(payload.overtime_share_change_pp === null ? [] : [{ label: `Change vs ${payload.year - 1}`, value: formatPercentagePoints(payload.overtime_share_change_pp) }]),
    ],
    note: payload.city === 'Chicago' ? 'Analyst-classified pay elements' : 'Published overtime field',
  }
  return (
    <g
      className="trend-point"
      tabIndex={0}
      role="button"
      aria-label={`${payload.city}, ${payload.year}, overtime share ${formatPercent(payload.overtime_share)}`}
      aria-describedby="data-tooltip"
      onFocus={(event) => show(event, tooltip)}
      onBlur={hide}
      onMouseEnter={(event) => show(event, tooltip)}
      onMouseMove={(event) => show(event, tooltip)}
      onMouseLeave={hide}
    >
      <circle cx={cx} cy={cy} r={latest ? 6 : 4.5} fill={latest ? '#0b4e9b' : '#a7afb7'} stroke="#fff" strokeWidth={2} />
      <text x={cx + (latest ? 10 : 0)} y={cy - 11} textAnchor={latest ? 'start' : 'middle'} className={latest ? 'chart-value latest' : 'chart-value'}>
        {formatPercent(payload.overtime_share)}
      </text>
    </g>
  )
}

export function TrendChart() {
  const years = story.metadata.included_years
  return (
    <div className="chart-shell trend-chart" role="group" aria-label="Overtime share of reported pay by city from 2023 through 2025; focus each point for details">
      <ResponsiveContainer width="100%" height={430}>
        <LineChart margin={{ top: 42, right: 72, bottom: 18, left: 4 }}>
          <CartesianGrid vertical={false} stroke="#e3e7ea" />
          <XAxis dataKey="year" type="number" domain={['dataMin', 'dataMax']} ticks={years} allowDecimals={false} tickLine={false} axisLine={{ stroke: '#89939c' }} />
          <YAxis domain={[0.06, 0.16]} ticks={[0.06, 0.08, 0.10, 0.12, 0.14, 0.16]} tickFormatter={(value) => formatPercent(value, 0)} tickLine={false} axisLine={false} width={46} />
          {cities.map((city) => (
            <Line
              key={city}
              data={story.city_years.filter((row) => row.city === city)}
              dataKey="overtime_share"
              name={city}
              type="linear"
              stroke={cityColor[city]}
              strokeOpacity={0.55}
              strokeWidth={2}
              isAnimationActive={false}
              dot={<TrendDot />}
              activeDot={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
      <div className="direct-legend" aria-hidden="true">
        {cities.map((city) => <span key={city}><i style={{ background: cityColor[city] }} />{city}</span>)}
      </div>
    </div>
  )
}
