export type City = 'Chicago' | 'New York City' | 'San Francisco'

export interface Source {
  city: City
  dataset_url: string
  api_url: string
}

export interface CityYear {
  city: City
  year: number
  basis: string
  source_records: number
  regular_pay_usd: number
  overtime_pay_usd: number
  other_pay_usd: number
  total_pay_usd: number
  overtime_share: number
  classification: string
  overtime_change_usd: number | null
  overtime_share_change_pp: number | null
}

export interface DepartmentYear {
  city: City
  year: number
  department: string
  total_pay_usd: number
  overtime_pay_usd: number
  share_of_city_overtime: number
  overtime_share_of_department_pay: number
  overtime_change_usd: number | null
  rank?: number
}

export interface Driver {
  city: City
  year: number
  department: string
  overtime_change_usd: number
  overtime_pay_usd: number
  share_of_city_overtime: number
  overtime_share_of_department_pay: number | null
}

export interface SensitivityScenario {
  scenario: string
  year: number
  overtime_share: number
  excluded_amount_usd: number
}

export interface StoryData {
  version: number
  metadata: {
    retrieved_at_utc: string
    included_years: number[]
    latest_complete_year: number
    excluded_incomplete_years: number[]
    headline_supported: boolean
    record_scope: string
  }
  definitions: {
    overtime_share: string
    department_driver: string
    classification_note: string
  }
  sources: Source[]
  period_coverage: Array<Record<string, string>>
  city_years: CityYear[]
  department_years: DepartmentYear[]
  top_departments: DepartmentYear[]
  concentrations: Array<{ city: City; year: number; top_five_share: number }>
  drivers: Driver[]
  chicago_sensitivity: SensitivityScenario[]
}

export interface TooltipItem {
  label: string
  value: string
}

export interface TooltipContent {
  title: string
  items: TooltipItem[]
  note?: string
}
