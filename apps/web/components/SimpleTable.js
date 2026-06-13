export default function SimpleTable({ columns, rows, emptyMessage = "No data available yet." }) {
  if (!rows.length) {
    return (
      <div className="rounded-3xl border border-dashed border-[var(--border)] bg-[color:var(--mist)] px-5 py-8 text-sm text-[color:var(--muted)]">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-[28px] border border-[var(--border)] bg-white shadow-panel">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-[var(--border)]">
          <thead className="bg-[color:var(--mist)]">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  className="px-4 py-3 text-left text-xs uppercase tracking-[0.16em] text-[color:var(--muted)]"
                >
                  {column.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border)]">
            {rows.map((row, rowIndex) => (
              <tr key={row.id || row.key || rowIndex} className="align-top">
                {columns.map((column) => (
                  <td key={column.key} className="px-4 py-4 text-sm leading-7 text-ink">
                    {column.render ? column.render(row[column.key], row) : row[column.key] || "-"}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
