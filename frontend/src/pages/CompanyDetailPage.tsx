import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import {
  getCompany,
  getCompanyActivity,
  getOpportunityActivity,
  type ActivityEntry,
  type CompanyDetail,
  type OpportunitySummary,
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
              <ActivityPanel companyId={company.id} opportunity={selectedOpportunity} />
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
}: {
  companyId: number;
  opportunity: OpportunitySummary;
}) {
  const [tab, setTab] = useState<"opportunity" | "company">("opportunity");
  const [entries, setEntries] = useState<ActivityEntry[]>([]);

  useEffect(() => {
    setTab("opportunity");
  }, [opportunity.id]);

  useEffect(() => {
    const load = tab === "opportunity" ? getOpportunityActivity(opportunity.id) : getCompanyActivity(companyId);
    load.then(setEntries).catch(() => setEntries([]));
  }, [tab, opportunity.id, companyId]);

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
