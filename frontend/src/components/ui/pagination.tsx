import { Button } from "@/components/ui/button";

interface PaginationProps {
  /** 0-indexed current page. */
  page: number;
  pageCount: number;
  onPageChange: (page: number) => void;
  disabled?: boolean;
}

type PageToken = number | "ellipsis";

function pageTokens(page: number, pageCount: number): PageToken[] {
  const current = page + 1;
  const delta = 1;
  const left = Math.max(2, current - delta);
  const right = Math.min(pageCount - 1, current + delta);

  const tokens: PageToken[] = [1];
  if (left > 2) tokens.push("ellipsis");
  for (let n = left; n <= right; n++) tokens.push(n);
  if (right < pageCount - 1) tokens.push("ellipsis");
  if (pageCount > 1) tokens.push(pageCount);

  return tokens;
}

export function Pagination({ page, pageCount, onPageChange, disabled }: PaginationProps) {
  if (pageCount <= 1) return null;

  return (
    <nav className="flex flex-wrap items-center gap-1" aria-label="Pagination">
      <Button
        variant="outline"
        size="sm"
        disabled={disabled || page === 0}
        onClick={() => onPageChange(page - 1)}
      >
        Previous
      </Button>

      {pageTokens(page, pageCount).map((token, i) =>
        token === "ellipsis" ? (
          <span key={`ellipsis-${i}`} className="px-1.5 text-sm text-muted-foreground">
            …
          </span>
        ) : (
          <Button
            key={token}
            variant={token === page + 1 ? "default" : "outline"}
            size="sm"
            className="w-9 px-0"
            disabled={disabled}
            aria-current={token === page + 1 ? "page" : undefined}
            onClick={() => onPageChange(token - 1)}
          >
            {token}
          </Button>
        ),
      )}

      <Button
        variant="outline"
        size="sm"
        disabled={disabled || page >= pageCount - 1}
        onClick={() => onPageChange(page + 1)}
      >
        Next
      </Button>
    </nav>
  );
}

export function PaginationFooter({
  page,
  pageSize,
  itemCount,
  total,
  onPageChange,
  disabled,
}: {
  page: number;
  pageSize: number;
  itemCount: number;
  total: number;
  onPageChange: (page: number) => void;
  disabled?: boolean;
}) {
  const rangeStart = total === 0 ? 0 : page * pageSize + 1;
  const rangeEnd = page * pageSize + itemCount;
  const pageCount = Math.ceil(total / pageSize);

  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <p className="text-xs text-muted-foreground">
        Showing {rangeStart}–{rangeEnd} of {total}
      </p>
      <Pagination page={page} pageCount={pageCount} onPageChange={onPageChange} disabled={disabled} />
    </div>
  );
}
