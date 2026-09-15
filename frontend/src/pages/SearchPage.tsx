import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Search } from "lucide-react";

import { Input } from "@/components/ui/input";
import { PaginationFooter } from "@/components/ui/pagination";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { searchCompanies, type CompanySearchResult } from "@/lib/api";

const PAGE_SIZE = 15;

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const [results, setResults] = useState<CompanySearchResult[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function handleQueryChange(value: string) {
    setQuery(value);
    setPage(0);
  }

  useEffect(() => {
    const trimmed = query.trim();
    setLoading(true);
    const timeout = setTimeout(() => {
      searchCompanies(trimmed, { limit: PAGE_SIZE, offset: page * PAGE_SIZE })
        .then((result) => {
          setResults(result.items);
          setTotal(result.total);
          setError(null);
        })
        .catch((err: unknown) => {
          setError(err instanceof Error ? err.message : "Search failed");
        })
        .finally(() => setLoading(false));
    }, 250);

    return () => clearTimeout(timeout);
  }, [query, page]);

  const trimmedQuery = query.trim();

  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-6 p-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Exhibition Sales CRM</h1>
          <p className="text-sm text-muted-foreground">
            Browse exhibitors, or search by name or code.
          </p>
        </div>
        <Link to="/follow-ups" className="shrink-0 text-sm text-muted-foreground hover:underline">
          Follow-ups
        </Link>
      </div>

      <div className="relative">
        <Search className="absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <label htmlFor="company-search" className="sr-only">
          Search company name, contact name, or code
        </label>
        <Input
          id="company-search"
          placeholder="Search company name, contact name, or code…"
          className="pl-9"
          value={query}
          onChange={(e) => handleQueryChange(e.target.value)}
        />
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {loading && (
        <p className="text-sm text-muted-foreground">
          {trimmedQuery ? "Searching…" : "Loading…"}
        </p>
      )}

      {!loading && results.length === 0 && !error && (
        <p className="text-sm text-muted-foreground">
          {trimmedQuery ? `No matches for "${query}".` : "No companies found."}
        </p>
      )}

      {results.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>{trimmedQuery ? `Results (${total})` : `Companies (${total})`}</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Company</TableHead>
                  <TableHead>Code</TableHead>
                  <TableHead>Region</TableHead>
                  <TableHead>Sales rep</TableHead>
                  <TableHead>Matched contact</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {results.map((company) => (
                  <TableRow key={company.id}>
                    <TableCell>
                      <Link
                        to={`/companies/${company.id}`}
                        className="rounded-sm font-medium outline-none hover:underline focus-visible:ring-2 focus-visible:ring-ring/50"
                      >
                        {company.company_name}
                      </Link>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {company.company_code}
                    </TableCell>
                    <TableCell>{company.region ?? "—"}</TableCell>
                    <TableCell>{company.sales_rep ?? "—"}</TableCell>
                    <TableCell>
                      {company.matched_contact
                        ? `${company.matched_contact.first_name ?? ""} ${company.matched_contact.last_name ?? ""}`.trim()
                        : "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            {total > PAGE_SIZE && (
              <PaginationFooter
                page={page}
                pageSize={PAGE_SIZE}
                itemCount={results.length}
                total={total}
                onPageChange={setPage}
                disabled={loading}
              />
            )}
          </CardContent>
        </Card>
      )}
    </main>
  );
}
