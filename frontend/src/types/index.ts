export type LeadStatus =
  | "pending"
  | "interested"
  | "not_interested"
  | "callback_requested"
  | "unreachable";

export type FundCategory = "equity" | "debt" | "hybrid" | "index" | "elss" | "unknown";

export interface Lead {
  id: string;
  name: string;
  phone_number: string;
  email: string | null;
  status: LeadStatus;
  fund_preference: FundCategory;
  notes: string | null;
  livekit_room: string | null;
  created_at: string;
  updated_at: string;
}

export interface DialResponse {
  room_name: string;
  participant_token: string;
  livekit_url: string;
}

export interface LeadListResponse {
  total: number;
  page: number;
  page_size: number;
  items: Lead[];
}
