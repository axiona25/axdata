// TypeScript types for dataset and DS-SPEC

export interface DatasetPlan {
  domain: string;
  title: string;
  sources: Array<{
    connector: string;
    queries: Array<Record<string, any>>;
  }>;
  transformations?: Array<Record<string, any>>;
  outputs?: string[];
  methodology?: string;
  license?: string;
  citation?: string;
  geographic_coverage?: string;
  temporal_coverage?: string;
  version?: string;
  indicators_metadata?: Record<string, Record<string, any>>;
}

export interface DatasetSpec {
  version: "1.0";
  request: {
    query_text: string;
    language: string;
    user_role?: "general" | "researcher" | "data_scientist";
  };
  sector: string;
  subsector?: string | null;
  dimensions: {
    time: {
      enabled: boolean;
      start?: string | null;
      end?: string | null;
      granularity: "hour" | "day" | "week" | "month" | "quarter" | "year" | "none";
    };
    geo: {
      enabled: boolean;
      scope?: string | null;
      level: "global" | "country" | "region" | "province" | "city" | "point" | "polygon" | "none";
      crs?: string;
    };
    entity: {
      kind: "none" | "person" | "organization" | "facility" | "country" | "region" | "product" | "study" | "document" | "custom";
      tracking: boolean;
      id_strategy?: "native" | "mapped" | "hash";
    };
  };
  variables: Array<{
    name: string;
    type: "numeric" | "categorical" | "text" | "event" | "geo";
    unit?: string | null;
    preferred_sources?: string[];
  }>;
  output: {
    template: "tabular" | "time_series" | "cross_sectional" | "panel" | "geospatial" | "text" | "event" | "hybrid" | "auto";
    formats: Array<"csv" | "parquet" | "json" | "geojson">;
    quality: {
      min_completeness?: number;
      deduplicate?: boolean;
    };
    compliance: {
      allow_pii?: boolean;
      license_policy?: "strict" | "normal";
    };
  };
}

export interface Dataset {
  id: string;
  user_id: string;
  chat_session_id?: string | null;
  title: string;
  domain: string;
  status: "draft" | "running" | "ready_for_payment" | "paid" | "delivered" | "failed";
  error_message?: string | null;
  created_at: string;
  updated_at: string;
  plan_json?: any;
}

export interface DatasetDetail extends Dataset {
  provenance?: {
    sources_used: Array<{
      source_id: string;
      name: string;
      authority: {
        level: number;
        publisher: string;
        badge: string;
      };
    }>;
    api_endpoints: Array<{
      source_id: string;
      path: string;
      method: string;
      parameters: Record<string, any>;
    }>;
    timeline: Array<{
      step: string;
      timestamp: string;
    }>;
    transformations_applied: string[];
    reproducibility: {
      ds_spec_hash: string;
      pipeline_version: string;
      pipeline_flow: string;
      reproduction_instructions: string;
    };
  };
  quality?: {
    quality_score: {
      overall_score: number;
      percentage: number;
      status: string;
      status_description: string;
    };
    completeness: {
      records_expected: number;
      records_available: number;
      completeness_percentage: number;
    };
    missing_values_analysis: Record<string, {
      completeness: number;
      missing_percentage: number;
      missing_count: number;
      warning: boolean;
    }>;
    outliers: {
      detected: boolean;
      method: string;
      total_outliers: number;
      action: string;
    };
    cross_source_validation?: {
      multi_source: boolean;
      best_correlation?: number;
      status: string;
    };
    quality_notes: string;
  };
  compliance?: {
    usage_rights: {
      commercial_use: string;
      academic_use: string;
      attribution_required: string;
      status: string;
    };
    licenses: Array<{
      source_id: string;
      license_name: string;
      license_url: string;
      commercial_use: boolean;
    }>;
    pii: {
      personal_data_detected: boolean;
      pii_risk: string;
      gdpr_impact: string;
    };
    jurisdiction: {
      jurisdictions: string[];
      relevant_regulations: string[];
      primary_jurisdiction: string;
    };
    notes: string;
  };
}

// Explicit re-export to ensure Vite can see the exports
export type { DatasetPlan, DatasetSpec, Dataset, DatasetDetail };
