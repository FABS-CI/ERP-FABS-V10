import { useState, useMemo } from "react";

/**
 * useSortableData — tri local sur un tableau d'objets
 * @param {Array} items   - tableau de données
 * @param {string|null} defaultKey  - colonne par défaut (null = pas de tri)
 * @param {"asc"|"desc"} defaultDir
 * @returns {{ sorted, sortKey, sortDir, requestSort }}
 */
export function useSortableData(items = [], defaultKey = null, defaultDir = "asc") {
  const [sortKey, setSortKey] = useState(defaultKey);
  const [sortDir, setSortDir] = useState(defaultDir);

  const requestSort = (key) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  const sorted = useMemo(() => {
    if (!sortKey) return items;
    return [...items].sort((a, b) => {
      const av = a[sortKey] ?? "";
      const bv = b[sortKey] ?? "";
      const cmp =
        typeof av === "number" && typeof bv === "number"
          ? av - bv
          : String(av).localeCompare(String(bv), "fr", { sensitivity: "base" });
      return sortDir === "asc" ? cmp : -cmp;
    });
  }, [items, sortKey, sortDir]);

  return { sorted, sortKey, sortDir, requestSort };
}
