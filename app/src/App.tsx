import { lazy, Suspense } from 'react'
import { CompositionChart } from './CompositionChart'
import { DepartmentRankings, DriverCharts } from './DepartmentCharts'
import { cities, latestCityRows, latestYear, priorYear, story } from './data'
import { formatMoney, formatPercentagePoints, formatPercent, formatSignedMoney } from './format'
import { TooltipProvider } from './tooltip'

const TrendChart = lazy(() => import('./TrendChart').then((module) => ({ default: module.TrendChart })))

function Sensitivity() {
  const values = story.chicago_sensitivity
  const minimum = Math.min(...values.map((row) => row.overtime_share)) - 0.004
  const maximum = Math.max(...values.map((row) => row.overtime_share)) + 0.004
  return (
    <div className="sensitivity" role="img" aria-label="Chicago overtime-share sensitivity scenarios">
      <div className="sensitivity-line" />
      {values.map((row, index) => {
        const left = (row.overtime_share - minimum) / (maximum - minimum) * 100
        return (
          <div className={`scenario scenario-${index}`} style={{ left: `${left}%` }} key={row.scenario}>
            <b>{formatPercent(row.overtime_share)}</b>
            <i />
            <span>{row.scenario}</span>
          </div>
        )
      })}
    </div>
  )
}

function App() {
  const chicago = latestCityRows.find((row) => row.city === 'Chicago')!
  const sf = latestCityRows.find((row) => row.city === 'San Francisco')!
  const nyc = latestCityRows.find((row) => row.city === 'New York City')!
  const largestDecline = [...latestCityRows].sort((a, b) => (a.overtime_share_change_pp ?? 0) - (b.overtime_share_change_pp ?? 0))[0]
  const headline = story.metadata.headline_supported
    ? 'Overtime’s share of pay fell in all three cities—but different departments drove the change'
    : 'Overtime’s share of pay fell across all three cities from 2024 to 2025'

  return (
    <TooltipProvider>
      <header className="site-header">
        <a className="brand" href="#top">Municipal overtime: NYC, Chicago, and San Francisco</a>
        <nav aria-label="Report links">
          <a href="#methods">Methodology <span aria-hidden="true">›</span></a>
          <a href="https://github.com/DhruvShah-Dev/municipal-payroll-comparison">GitHub <span aria-hidden="true">›</span></a>
        </nav>
      </header>
      <main id="main">
        <section className="hero" id="top">
          <h1>{headline}</h1>
          <p className="deck">Municipal payroll records show a shared decline in overtime’s share of reported pay from {priorYear} to {latestYear}. The department patterns—and the accounting behind them—are not the same.</p>
          <p className="scope">{story.metadata.included_years[0]}–{latestYear} · official city payroll data · aggregate records only</p>
          <div className="metric-strip" aria-label={`${latestYear} overtime share by city`}>
            {[chicago, sf, nyc].map((row) => (
              <div key={row.city}>
                <strong>{formatPercent(row.overtime_share)}</strong>
                <b>{row.city}</b>
                <span>overtime share of pay in {latestYear}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="story-section" id="trend">
          <div className="section-heading">
            <h2>Overtime’s share of pay declined in every city</h2>
            <p>The common movement occurs between {priorYear} and {latestYear}; the three-year context shows that the path was not identical.</p>
          </div>
          <aside className="annotation"><b>{largestDecline.city} had the largest decline:</b> {formatPercentagePoints(largestDecline.overtime_share_change_pp ?? 0)} from {priorYear}.</aside>
          <Suspense fallback={<div className="chart-loading" aria-label="Loading overtime trend" />}>
            <TrendChart />
          </Suspense>
        </section>

        <section className="story-section" id="composition">
          <div className="section-heading">
            <h2>Most reported pay is regular pay</h2>
            <p>Overtime remains a meaningful slice, while Chicago’s analyst-classified pay elements make its composition less directly comparable.</p>
          </div>
          <CompositionChart />
        </section>

        <section className="story-section" id="departments">
          <div className="section-heading">
            <h2>A few departments explain most overtime spending</h2>
            <p>Police, fire, transportation, health, corrections, and sanitation dominate different parts of each city’s overtime profile.</p>
          </div>
          <DepartmentRankings />
        </section>

        <section className="story-section" id="drivers">
          <div className="section-heading">
            <h2>Department shifts reveal where overtime changed</h2>
            <p>Chicago and New York City spent less on overtime overall. San Francisco’s overtime dollars rose {formatMoney(sf.overtime_change_usd ?? 0)}, even as its share fell because total salary pay grew faster.</p>
          </div>
          <DriverCharts />
        </section>

        <section className="story-section sensitivity-section" id="sensitivity">
          <div className="section-heading">
            <h2>Chicago’s ranking depends on classification—not the direction of change</h2>
            <p>Removing the {formatMoney(story.chicago_sensitivity[1].excluded_amount_usd, 0)} prior-year retroactive pension element raises Chicago’s {latestYear} share, but it remains below {priorYear}.</p>
          </div>
          <Sensitivity />
        </section>

        <section className="story-section conclusion" id="interpretation">
          <h2>What this does—and does not—show</h2>
          <div className="conclusion-grid">
            <div>
              <h3>Supported conclusions</h3>
              <ul>
                <li>Overtime’s share of reported pay was lower in {latestYear} than {priorYear} in all three city datasets.</li>
                <li>Chicago overtime dollars fell {formatMoney(Math.abs(chicago.overtime_change_usd ?? 0))}; New York City fell {formatMoney(Math.abs(nyc.overtime_change_usd ?? 0))}; San Francisco rose {formatMoney(sf.overtime_change_usd ?? 0)}.</li>
                <li>A small group of departments accounts for most overtime spending, but the mix differs by city.</li>
              </ul>
            </div>
            <div>
              <h3>Limits</h3>
              <ul>
                <li>The figures show payroll amounts and department shifts, not the operational causes of overtime.</li>
                <li>They do not measure service levels, staffing adequacy, hours worked, productivity, or fairness.</li>
                <li>City responsibilities, reporting calendars, and Chicago’s pay-element classification differ.</li>
              </ul>
            </div>
          </div>
        </section>

        <details className="methods" id="methods">
          <summary>Methods, definitions, and sources</summary>
          <div className="methods-content">
            <h2>How the comparison was built</h2>
            <p><strong>Overtime share:</strong> {story.definitions.overtime_share}</p>
            <p>{story.definitions.classification_note}</p>
            <p>New York City and San Francisco use fiscal years ending June 30. Chicago uses 24 payroll periods, which do not necessarily match when the work was performed. The latest incomplete year ({story.metadata.excluded_incomplete_years.join(', ')}) is excluded automatically.</p>
            <p>The department driver is the change in each department’s overtime dollars from {priorYear} to {latestYear}. Displayed drivers reconcile to the citywide change through an “All other departments” remainder.</p>
            <h3>Official sources</h3>
            <ul className="source-list">
              {story.sources.map((source) => <li key={source.city}><a href={source.dataset_url}>{source.city} payroll dataset</a></li>)}
            </ul>
            <p className="retrieved">Aggregate snapshot retrieved {new Date(story.metadata.retrieved_at_utc).toLocaleString('en-US', { dateStyle: 'long', timeStyle: 'short', timeZone: 'America/New_York' })} ET.</p>
          </div>
        </details>
      </main>
      <footer>
        <p>Reproducible analysis: <a href="https://github.com/DhruvShah-Dev/municipal-payroll-comparison">view the code and aggregate data on GitHub</a>.</p>
        <p>{cities.join(' · ')}</p>
      </footer>
    </TooltipProvider>
  )
}

export default App
