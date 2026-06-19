export default function SimpleTable({ columns, rows, emptyMessage = "No data available yet." }) {
  if (!rows.length) {
    return (
      <div className="rounded-[18px] border border-dashed border-[rgba(62,54,46,0.14)] bg-[#f8f1e5] px-5 py-8 text-sm text-[rgba(62,54,46,0.62)]">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-[18px] border border-[rgba(62,54,46,0.14)] bg-[#fbf6eb]">
      <div className="overflow-x-auto">
        <table className="min-w-full border-separate border-spacing-0">
          <thead>
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  className="border-b border-[rgba(62,54,46,0.12)] bg-[#efe5d4] px-4 py-3 text-left text-[11px] uppercase tracking-[0.16em] text-[rgba(62,54,46,0.6)]"
                >
                  {column.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr
                key={row.id || row.key || rowIndex}
                className="align-top transition hover:bg-[rgba(255,255,255,0.5)]"
              >
                {columns.map((column) => (
                  <td
                    key={column.key}
                    className="border-b border-[rgba(62,54,46,0.08)] px-4 py-4 text-sm leading-6 text-[#3E362E]"
                  >
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
