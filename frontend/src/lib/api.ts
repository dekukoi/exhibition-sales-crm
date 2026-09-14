export interface ContactSummary {
  id: number;
  contact_code: string;
  first_name: string | null;
  last_name: string | null;
  email: string | null;
  phone: string | null;
}

export interface CompanySearchResult {
  id: number;
  company_code: string;
  company_name: string;
  region: string | null;
  sales_rep: string | null;
  matched_contact: ContactSummary | null;
}

export interface FairEditionSummary {
  id: number;
  fair_edition_code: string;
  fair_name: string;
  city: string | null;
  venue: string | null;
  starts_on: string | null;
  ends_on: string | null;
  max_stand_height_m: string | null;
}

export interface OpportunitySummary {
  id: number;
  opportunity_code: string;
  description: string | null;
  status: string | null;
  amount_eur: string | null;
  opened_on: string | null;
  expected_close_on: string | null;
  stand_area_sqm: string | null;
  client_budget_eur: string | null;
  requested_height_m: string | null;
  brief_notes: string | null;
  contact_id: number | null;
  fair_edition: FairEditionSummary;
}

export interface CompanyDetail {
  id: number;
  company_code: string;
  company_name: string;
  province_code: string | null;
  region: string | null;
  sales_rep: string | null;
  contacts: ContactSummary[];
  opportunities: OpportunitySummary[];
}

export interface ActivityEntry {
  id: number;
  entry_id: string;
  opportunity_id: number | null;
  activity_type: string;
  occurred_at: string | null;
  details: string | null;
  follow_up_on: string | null;
  completion_marker: boolean | null;
  legacy_author: string | null;
}

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) {
    throw new Error(`Request to ${path} failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function searchCompanies(q: string): Promise<CompanySearchResult[]> {
  return apiFetch(`/api/companies?q=${encodeURIComponent(q)}`);
}

export function getCompany(id: number): Promise<CompanyDetail> {
  return apiFetch(`/api/companies/${id}`);
}

export function getCompanyActivity(id: number): Promise<ActivityEntry[]> {
  return apiFetch(`/api/companies/${id}/activity`);
}

export function getOpportunityActivity(id: number): Promise<ActivityEntry[]> {
  return apiFetch(`/api/opportunities/${id}/activity`);
}
