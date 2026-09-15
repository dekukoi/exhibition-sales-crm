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

export interface CompanySearchListResult {
  items: CompanySearchResult[];
  total: number;
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

export interface OpportunityUpdatePayload {
  status?: string | null;
  amount_eur?: string | null;
  opened_on?: string | null;
  expected_close_on?: string | null;
  stand_area_sqm?: string | null;
  client_budget_eur?: string | null;
  requested_height_m?: string | null;
  brief_notes?: string | null;
}

export type ActivityType = "call" | "email" | "meeting" | "note" | "task";

export interface ActivityCreatePayload {
  activity_type: ActivityType;
  details?: string | null;
  follow_up_on?: string | null;
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

export interface FollowUpItem {
  id: number;
  follow_up_on: string;
  activity_type: string;
  details: string | null;
  occurred_at: string | null;
  legacy_author: string | null;
  company_id: number;
  company_name: string;
  sales_rep: string | null;
  opportunity_id: number | null;
  opportunity_code: string | null;
}

export interface FollowUpListResult {
  items: FollowUpItem[];
  has_more: boolean;
  total: number;
}

export interface HandoffPreparerOutput {
  simulated: boolean;
  proposed_next_step: string;
}

export interface HandoffCheckerOutput {
  simulated: boolean;
  heads_up_ready: boolean;
  missing_fields: string[];
  edition_limit_known: boolean;
  height_within_limit: boolean | null;
  notes: string;
  validated_proposal: string;
}

export interface HandoffBrief {
  opportunity_id: number;
  opportunity_code: string;
  fair_name: string;
  fair_edition_code: string;
  max_stand_height_m: string | null;
  client_budget_eur: string | null;
  stand_area_sqm: string | null;
  requested_height_m: string | null;
  description: string | null;
  brief_notes: string | null;
}

export interface HandoffRunSummary {
  id: number;
  opportunity_id: number;
  created_at: string;
  brief: HandoffBrief;
  preparer_output: HandoffPreparerOutput;
  checker_output: HandoffCheckerOutput;
  verdict: "continue" | "stop";
  heads_up: boolean;
  reason: string;
  simulated: boolean;
}

export class ApiError extends Error {
  status: number;

  constructor(path: string, status: number) {
    super(`Request to ${path} failed: ${status}`);
    this.status = status;
  }
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  if (!res.ok) {
    throw new ApiError(path, res.status);
  }
  return res.json() as Promise<T>;
}

export function searchCompanies(
  q: string,
  params: { limit?: number; offset?: number } = {},
): Promise<CompanySearchListResult> {
  const query = new URLSearchParams({ q });
  if (params.limit) query.set("limit", String(params.limit));
  if (params.offset) query.set("offset", String(params.offset));
  return apiFetch(`/api/companies?${query.toString()}`);
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

export function listOpportunityStatuses(): Promise<string[]> {
  return apiFetch("/api/opportunities/statuses");
}

export function updateOpportunity(
  id: number,
  payload: OpportunityUpdatePayload,
): Promise<OpportunitySummary> {
  return apiFetch(`/api/opportunities/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function createActivity(
  opportunityId: number,
  payload: ActivityCreatePayload,
): Promise<ActivityEntry> {
  return apiFetch(`/api/opportunities/${opportunityId}/activity`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function listHandoffRuns(opportunityId: number): Promise<HandoffRunSummary[]> {
  return apiFetch(`/api/opportunities/${opportunityId}/handoff-runs`);
}

export function triggerHandoffRun(opportunityId: number): Promise<HandoffRunSummary> {
  return apiFetch(`/api/opportunities/${opportunityId}/handoff-runs`, { method: "POST" });
}

export function listFollowUps(params: {
  salesRep?: string;
  company?: string;
  dueBefore?: string;
  limit?: number;
  offset?: number;
}): Promise<FollowUpListResult> {
  const query = new URLSearchParams();
  if (params.salesRep) query.set("sales_rep", params.salesRep);
  if (params.company) query.set("company", params.company);
  if (params.dueBefore) query.set("due_before", params.dueBefore);
  if (params.limit) query.set("limit", String(params.limit));
  if (params.offset) query.set("offset", String(params.offset));
  return apiFetch(`/api/follow-ups?${query.toString()}`);
}

export function listFollowUpSalesReps(): Promise<string[]> {
  return apiFetch("/api/follow-ups/sales-reps");
}

export function completeFollowUp(id: number): Promise<FollowUpItem> {
  return apiFetch(`/api/follow-ups/${id}/complete`, { method: "POST" });
}
