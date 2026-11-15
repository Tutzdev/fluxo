/** The API's JSON, as it arrives. Money comes as strings ("-45.90") so no cent is lost to floating point. */

export type Money = string

export interface User {
  id: number
  name: string
  email: string
}

export interface Session {
  token: string
  expires_at: string
  user: User
}

export type AccountKind = 'checking' | 'savings' | 'credit_card' | 'cash'

export interface Account {
  id: number
  name: string
  kind: AccountKind
  opening_balance: Money
  balance: Money
  transaction_count: number
}

export type CategoryKind = 'expense' | 'income' | 'transfer'

export interface Rule {
  id: number
  pattern: string
}

export interface Category {
  id: number
  name: string
  kind: CategoryKind
  color: string
  rules: Rule[]
}

export type CategorySource = 'manual' | 'rule' | 'model'

export interface Transaction {
  id: number
  account_id: number
  occurred_on: string
  description: string
  amount: Money
  category_id: number | null
  category_source: CategorySource | null
  category_confidence: string | null
  needs_review: boolean
}

export interface TransactionPage {
  items: Transaction[]
  total: number
  page: number
  page_size: number
  income: Money
  expenses: Money
}

export interface CategorizationSummary {
  by_rule: number
  by_model: number
  left_for_review: number
}

export interface StatementImport {
  id: number
  account_id: number
  filename: string
  file_format: 'csv' | 'ofx'
  imported_count: number
  duplicate_count: number
  categorized_count: number
  created_at: string
}

export type BudgetStatus = 'on_track' | 'warning' | 'exceeded'

export interface Budget {
  category_id: number
  category_name: string
  color: string
  monthly_limit: Money
  spent: Money
  remaining: Money
  percent_used: number
  status: BudgetStatus
}

export interface Summary {
  month: string
  income: Money
  expenses: Money
  net: Money
  needs_review: number
  by_category: { category_id: number | null; name: string; color: string; amount: Money }[]
}

export interface MonthTotals {
  month: string
  income: Money
  expenses: Money
  net: Money
}

export interface Forecast {
  today: string
  days_left: number
  balance_now: Money
  expected_income: Money
  expected_bills: Money
  projected_day_to_day: Money
  projected_end_balance: Money
  upcoming: { description: string; amount: Money; expected_day: number; category_id: number | null; months_seen: number }[]
}
