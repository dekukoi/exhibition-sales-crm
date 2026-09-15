import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { PaginationFooter } from "@/components/ui/pagination";
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
const PAGE_SIZE = 8;

export default function FollowUpsPage() {
  const [salesReps, setSalesReps] = useState<string[]>([]);
  const [salesRep, setSalesRep] = useState("");
  const [company, setCompany] = useState("");
  const [page, setPage] = useState(0);
  const [items, setItems] = useState<FollowUpItem[]>([]);
  const [total, setTotal] = useState(0);
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
      listFollowUps({
        salesRep: salesRep || undefined,
        company: company.trim() || undefined,
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      })
        .then((result) => {
          setItems(result.items);
          setTotal(result.total);
          setError(null);
        })
        .catch((err: unknown) => {
          setError(err instanceof Error ? err.message : "Failed to load follow-ups");
        })
        .finally(() => setLoading(false));
    }, 250);

    return () => clearTimeout(timeout);
  }, [salesRep, company, page]);

  function handleSalesRepChange(value: string) {
    setSalesRep(value);
    setPage(0);
  }

  function handleCompanyChange(value: string) {
    setCompany(value);
    setPage(0);
  }

  async function handleComplete(id: number) {
    setCompletingId(id);
    try {
      await completeFollowUp(id);
      setItems((current) => current.filter((item) => item.id !== id));
      setTotal((current) => Math.max(0, current - 1));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to mark complete");
    } finally {
      setCompletingId(null);
    }
  }

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 p-8">
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
          onChange={(e) => handleSalesRepChange(e.target.value)}
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
          onChange={(e) => handleCompanyChange(e.target.value)}
        />
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <Card>
        <CardHeader>
          <CardTitle>Pending ({total})</CardTitle>
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

          {total > 0 && (
            <PaginationFooter
              page={page}
              pageSize={PAGE_SIZE}
              itemCount={items.length}
              total={total}
              onPageChange={setPage}
              disabled={loading}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
