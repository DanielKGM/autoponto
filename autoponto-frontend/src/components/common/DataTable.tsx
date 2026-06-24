import {
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export type DataTableAlign = "left" | "center" | "right";

export type DataTableColumn<TItem, TContext = unknown> = {
  key: string;
  label: string;
  align?: DataTableAlign;
  sortable?: boolean;
  sortValue?: (item: TItem, context: TContext) => unknown;
  render?: (item: TItem, context: TContext) => ReactNode;
};

type SortState = {
  key: string;
  direction: "asc" | "desc";
} | null;

type DataTableProps<TItem, TContext = unknown> = {
  columns: DataTableColumn<TItem, TContext>[];
  rows: TItem[];
  context: TContext;
  emptyState: ReactNode;
  actionsHeader?: string;
  className?: string;
  pageSize?: number;
  rowActions?: (item: TItem) => ReactNode;
  rowKey?: (item: TItem) => string | number;
  search?: string;
};

const DEFAULT_PAGE_SIZE = 10;

function valueText(value: unknown) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "boolean") return value ? "Sim" : "Não";
  if (Array.isArray(value)) return value.join(", ");
  return String(value);
}

function sortText(value: unknown) {
  if (value === null || value === undefined) return "";
  if (typeof value === "boolean") return value ? 1 : 0;
  if (typeof value === "number") return value;
  if (Array.isArray(value)) return value.join(" ");
  return String(value).toLocaleLowerCase("pt-BR");
}

function compareValues(left: unknown, right: unknown) {
  const a = sortText(left);
  const b = sortText(right);
  if (typeof a === "number" && typeof b === "number") return a - b;
  return String(a).localeCompare(String(b), "pt-BR", {
    numeric: true,
    sensitivity: "base",
  });
}

function columnSortValue<TItem, TContext>(
  column: DataTableColumn<TItem, TContext>,
  item: TItem,
  context: TContext,
) {
  if (column.sortValue) return column.sortValue(item, context);
  if (column.render) {
    const rendered = column.render(item, context);
    if (
      typeof rendered === "string"
      || typeof rendered === "number"
      || typeof rendered === "boolean"
    ) {
      return rendered;
    }
  }
  return (item as Record<string, unknown>)[column.key];
}

function defaultRowKey<TItem>(item: TItem, index: number) {
  const id = (item as Record<string, unknown>).id;
  return typeof id === "string" || typeof id === "number" ? id : index;
}

export function DataTable<TItem, TContext = unknown>({
  columns,
  rows,
  context,
  emptyState,
  actionsHeader = "Ações",
  className = "",
  pageSize = DEFAULT_PAGE_SIZE,
  rowActions,
  rowKey,
  search = "",
}: DataTableProps<TItem, TContext>) {
  const [sortState, setSortState] = useState<SortState>(null);
  const [tablePage, setTablePage] = useState(1);

  const filteredRows = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return rows;
    return rows.filter((row) => JSON.stringify(row).toLowerCase().includes(query));
  }, [rows, search]);

  const displayedRows = useMemo(() => {
    if (!sortState) return filteredRows;
    const column = columns.find((item) => item.key === sortState.key);
    if (!column || column.sortable === false) return filteredRows;
    const direction = sortState.direction === "asc" ? 1 : -1;
    return [...filteredRows].sort((left, right) => {
      const leftValue = columnSortValue(column, left, context);
      const rightValue = columnSortValue(column, right, context);
      return compareValues(leftValue, rightValue) * direction;
    });
  }, [columns, context, filteredRows, sortState]);

  const pageCount = Math.max(1, Math.ceil(displayedRows.length / pageSize));
  const currentPage = Math.min(tablePage, pageCount);
  const pageStart = displayedRows.length === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const pageEnd = Math.min(currentPage * pageSize, displayedRows.length);
  const pageRows = displayedRows.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  const pageButtons = useMemo(() => {
    if (pageCount <= 7) return Array.from({ length: pageCount }, (_, index) => index + 1);
    const pages = new Set([1, pageCount, currentPage - 1, currentPage, currentPage + 1]);
    return Array.from(pages)
      .filter((page) => page >= 1 && page <= pageCount)
      .sort((a, b) => a - b)
      .reduce<Array<number | "ellipsis">>((items, page) => {
        const last = items[items.length - 1];
        if (typeof last === "number" && page - last > 1) items.push("ellipsis");
        items.push(page);
        return items;
      }, []);
  }, [currentPage, pageCount]);

  useEffect(() => {
    setTablePage(1);
  }, [search, sortState, rows]);

  useEffect(() => {
    if (tablePage > pageCount) setTablePage(pageCount);
  }, [pageCount, tablePage]);

  function toggleSort(column: DataTableColumn<TItem, TContext>) {
    if (column.sortable === false) return;
    setSortState((current) => {
      if (current?.key !== column.key) return { key: column.key, direction: "asc" };
      if (current.direction === "asc") return { key: column.key, direction: "desc" };
      return null;
    });
  }

  if (displayedRows.length === 0) return <>{emptyState}</>;

  return (
    <>
      <div className="table-responsive">
        <table className={`table data-table ${className}`.trim()} data-datatable>
          <thead>
            <tr>
              {columns.map((column) => {
                const isSorted = sortState?.key === column.key;
                const ariaSort = isSorted
                  ? sortState.direction === "asc" ? "ascending" : "descending"
                  : "none";
                return (
                  <th
                    key={column.key}
                    className={column.align ? `admin-cell-${column.align}` : undefined}
                    aria-sort={ariaSort}
                  >
                    {column.sortable === false ? (
                      column.label
                    ) : (
                      <button
                        type="button"
                        className={`table-sort table-sort-${column.align || "left"} ${
                          isSorted ? `active sort-${sortState.direction}` : ""
                        }`}
                        onClick={() => toggleSort(column)}
                      >
                        <span>{column.label}</span>
                        <span className="table-sort-indicator" aria-hidden="true" />
                      </button>
                    )}
                  </th>
                );
              })}
              {rowActions && <th className="admin-cell-center" data-orderable="false">{actionsHeader}</th>}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, index) => (
              <tr key={rowKey ? rowKey(row) : defaultRowKey(row, index)}>
                {columns.map((column) => (
                  <td
                    key={column.key}
                    className={column.align ? `admin-cell-${column.align}` : undefined}
                  >
                    {column.render
                      ? column.render(row, context)
                      : valueText((row as Record<string, unknown>)[column.key])}
                  </td>
                ))}
                {rowActions && (
                  <td className="admin-cell-center">
                    <div className="admin-row-actions">
                      {rowActions(row)}
                    </div>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="dt-layout-row admin-table-footer">
        <div className="dt-info">
          Mostrando {pageStart}-{pageEnd} de {displayedRows.length}
        </div>
        <div className="dt-paging" aria-label="Paginação da tabela">
          <button
            type="button"
            className={`dt-paging-button ${currentPage === 1 ? "disabled" : ""}`}
            onClick={() => setTablePage((page) => Math.max(1, page - 1))}
            disabled={currentPage === 1}
          >
            {"<"}
          </button>
          {pageButtons.map((page, index) => page === "ellipsis" ? (
            <span className="ellipsis" key={`ellipsis-${index}`}>...</span>
          ) : (
            <button
              type="button"
              className={`dt-paging-button ${page === currentPage ? "current" : ""}`}
              key={page}
              onClick={() => setTablePage(page)}
              aria-current={page === currentPage ? "page" : undefined}
            >
              {page}
            </button>
          ))}
          <button
            type="button"
            className={`dt-paging-button ${currentPage === pageCount ? "disabled" : ""}`}
            onClick={() => setTablePage((page) => Math.min(pageCount, page + 1))}
            disabled={currentPage === pageCount}
          >
            {">"}
          </button>
        </div>
      </div>
    </>
  );
}
