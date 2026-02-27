// src/types/filters.ts
export interface FilterOption {
  filter_name: string;
}

export interface AllFilters {
  domains: FilterOption[];
  languages: FilterOption[];
  statuses: FilterOption[]; // optional if you don’t fetch them yet
  
  targets: FilterOption[];
  plans: FilterOption[];     
  metrics: FilterOption[];
}