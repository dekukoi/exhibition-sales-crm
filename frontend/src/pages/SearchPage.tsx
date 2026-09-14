import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Search } from "lucide-react";

import { Input } from "@/components/ui/input";
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

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<CompanySearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const trimmed = query.trim();
    if (!trimmed) {
      setResults([]);
      setError(null);
      return;
    }

    setLoading(true);
    const timeout = setTimeout(() => {
      searchCompanies(trimmed)
        .then((matches) => {
          setResults(matches);
          setError(null);
        })
        .catch((err: unknown) => {
          setError(err instanceof Error ? err.message : "Search failed");
        })
        .finally(() => setLoading(false));
    }, 250);

    return () => clearTimeout(timeout);
  }, [query]);

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6 p-8">
      <div>
        <h1 className="text-2xl font-semibold">Exhibition Sales CRM</h1>
        <p className="text-sm text-muted-foreground">
          Find an exhibitor or contact by name or code.
        </p>
      </div>

      <div className="relative">
        <Search className="absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          autoFocus
          placeholder="Search company name, contact name, or code…"
          className="pl-9"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {query.trim() && !loading && results.length === 0 && !error && (
        <p className="text-sm text-muted-foreground">No matches for "{query}".</p>
      )}

      {results.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Results</CardTitle>
          </CardHeader>
          <CardContent>
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
                        className="font-medium hover:underline"
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
          </CardContent>
        </Card>
      )}
    </div>
  );
}
