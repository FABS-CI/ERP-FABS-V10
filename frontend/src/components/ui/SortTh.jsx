import { ChevronUp, ChevronDown, ChevronsUpDown } from "lucide-react";

/**
 * SortTh — <th> cliquable avec indicateur de tri
 */
export default function SortTh({ label, sortKey, currentKey, currentDir, onSort, className = "" }) {
  const active = currentKey === sortKey;
  return (
    <th
      className={`px-4 py-3 font-semibold cursor-pointer select-none group whitespace-nowrap ${className}`}
      onClick={() => onSort(sortKey)}
    >
      <span className="inline-flex items-center gap-1">
        {label}
        <span className={`transition-opacity ${active ? "opacity-100" : "opacity-0 group-hover:opacity-50"}`}>
          {active ? (
            currentDir === "asc" ? (
              <ChevronUp className="w-3.5 h-3.5" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5" />
            )
          ) : (
            <ChevronsUpDown className="w-3.5 h-3.5" />
          )}
        </span>
      </span>
    </th>
  );
}
