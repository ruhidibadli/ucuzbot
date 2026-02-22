"use client";

import { stores } from "@/lib/constants";

interface StoreChipsProps {
  selectedStores: string[];
  onToggle: (slug: string) => void;
  onToggleAll: () => void;
}

export default function StoreChips({ selectedStores, onToggle, onToggleAll }: StoreChipsProps) {
  return (
    <>
      <div className="store-chips">
        {stores.map((store) => (
          <div
            key={store.slug}
            className={`store-chip ${selectedStores.includes(store.slug) ? "active" : ""}`}
            onClick={() => onToggle(store.slug)}
          >
            <span className="store-chip-check">
              {selectedStores.includes(store.slug) ? "\u2713" : ""}
            </span>
            {store.name}
          </div>
        ))}
      </div>
      <button type="button" className="store-select-all" onClick={onToggleAll}>
        {selectedStores.length === stores.length
          ? "Hamisini silin / Deselect all"
          : "Hamisini secin / Select all"}
      </button>
    </>
  );
}
