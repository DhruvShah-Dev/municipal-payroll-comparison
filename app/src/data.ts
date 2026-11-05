import rawData from '@story-data'
import type { City, StoryData } from './types'

export const story = rawData as StoryData
export const cities: City[] = ['Chicago', 'San Francisco', 'New York City']
export const latestYear = story.metadata.latest_complete_year
export const priorYear = story.metadata.included_years.at(-2) as number
export const latestCityRows = cities.map((city) => story.city_years.find((row) => row.city === city && row.year === latestYear)!)

export const cityColor: Record<City, string> = {
  Chicago: '#0b4e9b',
  'San Francisco': '#3d6f9f',
  'New York City': '#718ca8',
}
