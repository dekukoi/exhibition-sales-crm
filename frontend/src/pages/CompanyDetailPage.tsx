import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import {
  createActivity,
  getCompany,
  getCompanyActivity,
  getOpportunityActivity,
  listHandoffRuns,
  listOpportunityStatuses,
  triggerHandoffRun,
  updateOpportunity,
  type ActivityCreatePayload,
  type ActivityEntry,
  type ActivityType,
  type CompanyDetail,
  type HandoffRunSummary,
  type OpportunitySummary,
  type OpportunityUpdatePayload,
} from "@/lib/api";

function money(value: string | null, unit: string): string {
  if (value === null) return "—";
  return `${Number(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${unit}`;
}

export default function CompanyDetailPage() {
  const { id } = useParams<{ id: string }>();
  const companyId = Number(id);

  const [company, setCompany] = useState<CompanyDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedOpportunity, setSelectedOpportunity] = useState<OpportunitySummary | null>(
    null,
  );
  const [statuses, setStatuses] = useState<string[]>([]);
  const [activityRefreshKey, setActivityRefreshKey] = useState(0);

  useEffect(() => {
    setCompany(null);
    setSelectedOpportunity(null);
    getCompany(companyId)
      .then((detail) => {
        setCompany(detail);
        setSelectedOpportunity(detail.opportunities[0] ?? null);
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Failed to load"));
  }, [companyId]);

  useEffect(() => {
    listOpportunityStatuses()
      .then(setStatuses)
      .catch(() => setStatuses([]));
  }, []);

  function handleOpportunityUpdated(updated: OpportunitySummary) {
    setCompany((current) =>
      current
        ? {
            ...current,
            opportunities: current.opportunities.map((opp) =>
              opp.id === updated.id ? updated : opp,
            ),
          }
        : current,
    );
    setSelectedOpportunity(updated);
  }

  function handleActivityLogged() {
    setActivityRefreshKey((key) => key + 1);
  }

  if (error) return <p className="p-8 text-sm text-destructive">{error}</p>;
  if (!company) return <p className="p-8 text-sm text-muted-foreground">Loading…</p>;

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6 p-8">
      <Link
        to="/"
        className="flex w-fit items-center gap-1 text-sm text-muted-foreground hover:underline"
      >
        <ArrowLeft className="h-4 w-4" /> Back to search
      </Link>

      <div>
        <h1 className="text-2xl font-semibold">{company.company_name}</h1>
        <p className="text-sm text-muted-foreground">
          {company.company_code} · {company.region ?? "Unknown region"} · Sales rep:{" "}
          {company.sales_rep ?? "Unassigned"}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Contacts</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Code</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Phone</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {company.contacts.map((contact) => (
                <TableRow key={contact.id}>
                  <TableCell>
                    {contact.first_name} {contact.last_name}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {contact.contact_code}
                  </TableCell>
                  <TableCell>{contact.email ?? "—"}</TableCell>
                  <TableCell>{contact.phone ?? "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Opportunities</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Fair edition</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Value</TableHead>
                <TableHead>Opened</TableHead>
                <TableHead>Stand area</TableHead>
                <TableHead>Requested height</TableHead>
                <TableHead>Client budget</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {company.opportunities.map((opp) => (
                <TableRow
                  key={opp.id}
                  className={`cursor-pointer ${selectedOpportunity?.id === opp.id ? "bg-muted/50" : ""}`}
                  onClick={() => setSelectedOpportunity(opp)}
                >
                  <TableCell>
                    <div className="font-medium">{opp.fair_edition.fair_name}</div>
                    <div className="text-xs text-muted-foreground">
                      {opp.fair_edition.city} · {opp.fair_edition.starts_on} –{" "}
                      {opp.fair_edition.ends_on}
                    </div>
                  </TableCell>
                  <TableCell>
                    {opp.status ? <Badge variant="secondary">{opp.status}</Badge> : "—"}
                  </TableCell>
                  <TableCell>{money(opp.amount_eur, "€")}</TableCell>
                  <TableCell>{opp.opened_on ?? "—"}</TableCell>
                  <TableCell>{money(opp.stand_area_sqm, "m²")}</TableCell>
                  <TableCell>
                    {money(opp.requested_height_m, "m")}
                    {opp.requested_height_m &&
                      Number(opp.requested_height_m) >
                        Number(opp.fair_edition.max_stand_height_m ?? "0") && (
                        <Badge variant="outline" className="ml-2 border-destructive text-destructive">
                          exceeds {opp.fair_edition.max_stand_height_m}m limit
                        </Badge>
                      )}
                  </TableCell>
                  <TableCell>{money(opp.client_budget_eur, "€")}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {selectedOpportunity && (
            <>
              <Separator />
              <div className="flex flex-col gap-2 text-sm">
                <div className="font-medium">
                  {selectedOpportunity.opportunity_code} — {selectedOpportunity.description ?? "No description"}
                </div>
                {selectedOpportunity.brief_notes && (
                  <p className="text-muted-foreground">{selectedOpportunity.brief_notes}</p>
                )}
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <OpportunityEditForm
                  opportunity={selectedOpportunity}
                  statuses={statuses}
                  onUpdated={handleOpportunityUpdated}
                />
                <LogActivityForm
                  opportunity={selectedOpportunity}
                  onLogged={handleActivityLogged}
                />
              </div>

              <ActivityPanel
                companyId={company.id}
                opportunity={selectedOpportunity}
                refreshKey={activityRefreshKey}
              />

              <HandoffPanel opportunity={selectedOpportunity} />
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function ActivityPanel({
  companyId,
  opportunity,
  refreshKey,
}: {
  companyId: number;
  opportunity: OpportunitySummary;
  refreshKey: number;
}) {
  const [tab, setTab] = useState<"opportunity" | "company">("opportunity");
  const [entries, setEntries] = useState<ActivityEntry[]>([]);

  useEffect(() => {
    setTab("opportunity");
  }, [opportunity.id]);

  useEffect(() => {
    const load = tab === "opportunity" ? getOpportunityActivity(opportunity.id) : getCompanyActivity(companyId);
    load.then(setEntries).catch(() => setEntries([]));
  }, [tab, opportunity.id, companyId, refreshKey]);

  return (
    <Tabs value={tab} onValueChange={(v) => setTab(v as "opportunity" | "company")}>
      <TabsList>
        <TabsTrigger value="opportunity">This opportunity's conversations</TabsTrigger>
        <TabsTrigger value="company">Full company history</TabsTrigger>
      </TabsList>
      <TabsContent value={tab}>
        {entries.length === 0 ? (
          <p className="py-4 text-sm text-muted-foreground">No activity recorded.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Type</TableHead>
                <TableHead>When</TableHead>
                <TableHead>Details</TableHead>
                <TableHead>Follow-up</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Author</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {entries.map((entry) => (
                <TableRow key={entry.id}>
                  <TableCell className="capitalize">{entry.activity_type}</TableCell>
                  <TableCell>{entry.occurred_at?.slice(0, 16).replace("T", " ") ?? "—"}</TableCell>
                  <TableCell className="max-w-sm truncate">{entry.details ?? "—"}</TableCell>
                  <TableCell>{entry.follow_up_on ?? "—"}</TableCell>
                  <TableCell>
                    {entry.completion_marker === true && <Badge>Completed</Badge>}
                    {entry.completion_marker === false && (
                      <Badge variant="secondary">Pending</Badge>
                    )}
                    {entry.completion_marker === null && "—"}
                  </TableCell>
                  <TableCell>{entry.legacy_author ?? "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </TabsContent>
    </Tabs>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="flex flex-col gap-1 text-xs text-muted-foreground">
      {label}
      {children}
    </label>
  );
}

interface OpportunityFormFields {
  status: string;
  amount_eur: string;
  opened_on: string;
  expected_close_on: string;
  stand_area_sqm: string;
  client_budget_eur: string;
  requested_height_m: string;
  brief_notes: string;
}

function fieldsFromOpportunity(opportunity: OpportunitySummary): OpportunityFormFields {
  return {
    status: opportunity.status ?? "",
    amount_eur: opportunity.amount_eur ?? "",
    opened_on: opportunity.opened_on ?? "",
    expected_close_on: opportunity.expected_close_on ?? "",
    stand_area_sqm: opportunity.stand_area_sqm ?? "",
    client_budget_eur: opportunity.client_budget_eur ?? "",
    requested_height_m: opportunity.requested_height_m ?? "",
    brief_notes: opportunity.brief_notes ?? "",
  };
}

function toUpdatePayload(fields: OpportunityFormFields): OpportunityUpdatePayload {
  const payload: OpportunityUpdatePayload = {};
  for (const key of Object.keys(fields) as (keyof OpportunityFormFields)[]) {
    payload[key] = fields[key] || null;
  }
  return payload;
}

function OpportunityEditForm({
  opportunity,
  statuses,
  onUpdated,
}: {
  opportunity: OpportunitySummary;
  statuses: string[];
  onUpdated: (updated: OpportunitySummary) => void;
}) {
  const [fields, setFields] = useState<OpportunityFormFields>(() => fieldsFromOpportunity(opportunity));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setFields(fieldsFromOpportunity(opportunity));
    setError(null);
    setSaved(false);
  }, [opportunity.id]);

  function setField<K extends keyof OpportunityFormFields>(key: K, value: string) {
    setFields((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const updated = await updateOpportunity(opportunity.id, toUpdatePayload(fields));
      onUpdated(updated);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save opportunity");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Update opportunity</CardTitle>
      </CardHeader>
      <CardContent>
        <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Status">
              <Select value={fields.status} onChange={(e) => setField("status", e.target.value)}>
                <option value="">—</option>
                {statuses.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Value (€)">
              <Input
                type="number"
                step="0.01"
                value={fields.amount_eur}
                onChange={(e) => setField("amount_eur", e.target.value)}
              />
            </Field>
            <Field label="Opened">
              <Input
                type="date"
                value={fields.opened_on}
                onChange={(e) => setField("opened_on", e.target.value)}
              />
            </Field>
            <Field label="Expected close">
              <Input
                type="date"
                value={fields.expected_close_on}
                onChange={(e) => setField("expected_close_on", e.target.value)}
              />
            </Field>
            <Field label="Stand area (m²)">
              <Input
                type="number"
                step="0.01"
                value={fields.stand_area_sqm}
                onChange={(e) => setField("stand_area_sqm", e.target.value)}
              />
            </Field>
            <Field label="Requested height (m)">
              <Input
                type="number"
                step="0.01"
                value={fields.requested_height_m}
                onChange={(e) => setField("requested_height_m", e.target.value)}
              />
            </Field>
            <Field label="Client budget (€)">
              <Input
                type="number"
                step="0.01"
                value={fields.client_budget_eur}
                onChange={(e) => setField("client_budget_eur", e.target.value)}
              />
            </Field>
          </div>
          <Field label="Brief notes">
            <Textarea
              rows={3}
              value={fields.brief_notes}
              onChange={(e) => setField("brief_notes", e.target.value)}
            />
          </Field>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <div className="flex items-center gap-3">
            <Button type="submit" size="sm" disabled={saving} className="w-fit">
              {saving ? "Saving…" : "Save changes"}
            </Button>
            {saved && !saving && <span className="text-xs text-muted-foreground">Saved.</span>}
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

function LogActivityForm({
  opportunity,
  onLogged,
}: {
  opportunity: OpportunitySummary;
  onLogged: () => void;
}) {
  const [activityType, setActivityType] = useState<ActivityType>("call");
  const [details, setDetails] = useState("");
  const [followUpOn, setFollowUpOn] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setActivityType("call");
    setDetails("");
    setFollowUpOn("");
    setError(null);
  }, [opportunity.id]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const payload: ActivityCreatePayload = {
        activity_type: activityType,
        details: details.trim() || null,
        follow_up_on: followUpOn || null,
      };
      await createActivity(opportunity.id, payload);
      setDetails("");
      setFollowUpOn("");
      onLogged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to log activity");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Log a conversation</CardTitle>
      </CardHeader>
      <CardContent>
        <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
          <Field label="Type">
            <Select
              value={activityType}
              onChange={(e) => setActivityType(e.target.value as ActivityType)}
            >
              <option value="call">Call</option>
              <option value="email">Email</option>
              <option value="meeting">Meeting</option>
              <option value="note">Note</option>
              <option value="task">Task</option>
            </Select>
          </Field>
          <Field label="Details">
            <Textarea
              rows={3}
              placeholder="What was discussed…"
              value={details}
              onChange={(e) => setDetails(e.target.value)}
            />
          </Field>
          <Field label="Follow up on (optional)">
            <Input type="date" value={followUpOn} onChange={(e) => setFollowUpOn(e.target.value)} />
          </Field>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Button type="submit" size="sm" disabled={saving} className="w-fit">
            {saving ? "Saving…" : "Add to activity log"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function HandoffPanel({ opportunity }: { opportunity: OpportunitySummary }) {
  const [runs, setRuns] = useState<HandoffRunSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    listHandoffRuns(opportunity.id)
      .then(setRuns)
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : "Failed to load handoff runs"),
      )
      .finally(() => setLoading(false));
  }, [opportunity.id]);

  async function handleRun() {
    setTriggering(true);
    setError(null);
    try {
      const run = await triggerHandoffRun(opportunity.id);
      setRuns((current) => [run, ...current]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run the handoff assistant");
    } finally {
      setTriggering(false);
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-3">
        <CardTitle>Handoff assistant</CardTitle>
        <Button size="sm" onClick={handleRun} disabled={triggering}>
          {triggering ? "Running…" : "Run handoff assistant"}
        </Button>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <p className="text-xs text-muted-foreground">
          A deterministic, rule-based stand-in for a model response — not a real model call. Every
          run below is labeled simulated.
        </p>
        {error && <p className="text-sm text-destructive">{error}</p>}
        {loading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : runs.length === 0 ? (
          <p className="text-sm text-muted-foreground">No handoff runs yet for this opportunity.</p>
        ) : (
          <div className="flex flex-col gap-3">
            {runs.map((run) => (
              <HandoffRunCard key={run.id} run={run} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function HandoffRunCard({ run }: { run: HandoffRunSummary }) {
  return (
    <div className="flex flex-col gap-2 rounded-md border p-3 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <Badge
          variant={run.verdict === "continue" ? "default" : "outline"}
          className={run.verdict === "stop" ? "border-destructive text-destructive" : undefined}
        >
          {run.verdict}
        </Badge>
        {run.heads_up && <Badge variant="secondary">Heads-up</Badge>}
        <span className="text-xs text-muted-foreground">
          {run.created_at.slice(0, 16).replace("T", " ")}
        </span>
        <Badge variant="outline" className="ml-auto">
          simulated
        </Badge>
      </div>
      <p>{run.reason}</p>
      <Separator />
      <div className="grid gap-2 text-xs text-muted-foreground sm:grid-cols-2">
        <div>
          <div className="font-medium text-foreground">Preparer (simulated)</div>
          <p>{run.preparer_output.proposed_next_step}</p>
        </div>
        <div>
          <div className="font-medium text-foreground">Checker (simulated)</div>
          <p>{run.checker_output.notes}</p>
        </div>
      </div>
    </div>
  );
}
