import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  completeFollowUp,
  listFollowUps,
  listFollowUpSalesReps,
  type FollowUpItem,
} from "@/lib/api";

const today = () => new Date().toISOString().slice(0, 10);

export default function FollowUpsPage() {
  const [salesReps, setSalesReps] = useState<string[]>([]);
  const [salesRep, setSalesRep] = useState("");
  const [company, setCompany] = useState("");
  const [items, setItems] = useState<FollowUpItem[]>([]);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [completingId, setCompletingId] = useState<number | null>(null);

  useEffect(() => {
    listFollowUpSalesReps()
      .then(setSalesReps)
      .catch(() => setSalesReps([]));
  }, []);

  useEffect(() => {
    setLoading(true);
    const timeout = setTimeout(() => {
      listFollowUps({ salesRep: salesRep || undefined, company: company.trim() || undefined })
        .then((result) => {
          setItems(result.items);
          setHasMore(result.has_more);
          setError(null);
        })
        .catch((err: unknown) => {
          setError(err instanceof Error ? err.message : "Failed to load follow-ups");
        })
        .finally(() => setLoading(false));
    }, 250);

    return () => clearTimeout(timeout);
  }, [salesRep, company]);

  async function handleComplete(id: number) {
    setCompletingId(id);
    try {
      await completeFollowUp(id);
      setItems((current) => current.filter((item) => item.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to mark complete");
    } finally {
      setCompletingId(null);
    }
  }

  async function loadMore() {
    try {
      const result = await listFollowUps({
        salesRep: salesRep || undefined,
        company: company.trim() || undefined,
        offset: items.length,
      });
      setItems((current) => [...current, ...result.items]);
      setHasMore(result.has_more);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load more");
    }
  }

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6 p-8">
      <Link
        to="/"
        className="flex w-fit items-center gap-1 text-sm text-muted-foreground hover:underline"
      >
        <ArrowLeft className="h-4 w-4" /> Back to search
      </Link>

      <div>
        <h1 className="text-2xl font-semibold">Follow-ups</h1>
        <p className="text-sm text-muted-foreground">
          Pending follow-ups across all exhibitors, soonest due first.
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <Select
          className="w-48"
          value={salesRep}
          onChange={(e) => setSalesRep(e.target.value)}
        >
          <option value="">All sales reps</option>
          {salesReps.map((rep) => (
            <option key={rep} value={rep}>
              {rep}
            </option>
          ))}
        </Select>
        <Input
          placeholder="Filter by company name…"
          className="max-w-xs"
          value={company}
          onChange={(e) => setCompany(e.target.value)}
        />
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <Card>
        <CardHeader>
          <CardTitle>Pending ({items.length}{hasMore ? "+" : ""})</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : items.length === 0 ? (
            <p className="text-sm text-muted-foreground">No pending follow-ups.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Due</TableHead>
                  <TableHead>Company</TableHead>
                  <TableHead>Sales rep</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Details</TableHead>
                  <TableHead>Opportunity</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>
                      {item.follow_up_on}
                      {item.follow_up_on < today() && (
                        <Badge variant="outline" className="ml-2 border-destructive text-destructive">
                          overdue
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <Link
                        to={`/companies/${item.company_id}`}
                        className="font-medium hover:underline"
                      >
                        {item.company_name}
                      </Link>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {item.sales_rep ?? "—"}
                    </TableCell>
                    <TableCell className="capitalize">{item.activity_type}</TableCell>
                    <TableCell className="max-w-sm truncate">{item.details ?? "—"}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {item.opportunity_code ?? "—"}
                    </TableCell>
                    <TableCell>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={completingId === item.id}
                        onClick={() => handleComplete(item.id)}
                      >
                        Mark complete
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}

          {hasMore && (
            <Button variant="outline" size="sm" className="w-fit" onClick={loadMore}>
              Load more
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
