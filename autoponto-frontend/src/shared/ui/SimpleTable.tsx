import type { ReactNode } from "react";
import type { DataTableAlign } from "./DataTable";

export type SimpleTableColumn<TItem> = {
  key: string;
  label: string;
  align?: DataTableAlign;
  className?: string;
  render?: (item: TItem) => ReactNode;
  width?: string;
};

type SimpleTableProps<TItem> = {
  columns: SimpleTableColumn<TItem>[];
  rows: TItem[];
  emptyState: ReactNode;
  className?: string;
  rowKey: (item: TItem) => string | number;
};

function valueText(value: unknown) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "boolean") return value ? "Sim" : "Não";
  return String(value);
}

export function SimpleTable<TItem>({
  columns,
  rows,
  emptyState,
  className = "",
  rowKey,
}: SimpleTableProps<TItem>) {
  if (rows.length === 0) return <>{emptyState}</>;

  return (
    <div className="table-responsive">
      <table className={`table simple-table ${className}`.trim()}>
        <thead>
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className={[
                  column.align ? `admin-cell-${column.align}` : "",
                  column.className ?? "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                style={column.width ? { width: column.width } : undefined}
              >
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={rowKey(row)}>
              {columns.map((column) => (
                <td
                  key={column.key}
                  className={[
                    column.align ? `admin-cell-${column.align}` : "",
                    column.className ?? "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                >
                  {column.render
                    ? column.render(row)
                    : valueText((row as Record<string, unknown>)[column.key])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
