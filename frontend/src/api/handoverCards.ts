import type { CompletenessScore, SignResponse } from "../types";

export async function postConfirmMissing(
  cardId: string,
  item: string,
  value: "explicitly_none" | "addressed_separately" | "not_applicable"
): Promise<{ completeness: CompletenessScore }> {
  const res = await fetch(`/api/handover-cards/${cardId}/confirm-missing`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ item, value }),
  });
  if (!res.ok) throw new Error(`POST confirm-missing failed: ${res.status}`);
  return res.json() as Promise<{ completeness: CompletenessScore }>;
}

export async function postSign(
  cardId: string,
  signedBy: string
): Promise<SignResponse> {
  const res = await fetch(`/api/handover-cards/${cardId}/sign`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ signed_by: signedBy }),
  });
  if (!res.ok) throw new Error(`POST sign failed: ${res.status}`);
  return res.json() as Promise<SignResponse>;
}
