export const API_BASE = "/api/v1";

export const stores = [
  { slug: "kontakt", name: "Kontakt Home", type: "Elektronika", icon: "\u{1F3EA}" },
  { slug: "baku_electronics", name: "Baku Electronics", type: "Elektronika", icon: "\u{1F4BB}" },
  { slug: "irshad", name: "Irshad", type: "Elektronika", icon: "\u{1F4F1}" },
  { slug: "maxi", name: "Maxi.az", type: "Marketplace", icon: "\u{1F6D2}" },
  { slug: "tap_az", name: "Tap.az", type: "Elanlar", icon: "\u{1F4CB}" },
  { slug: "umico", name: "Umico", type: "Marketplace", icon: "\u{1F381}" },
];

export function urlBase64ToUint8Array(base64String: string): ArrayBuffer {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray.buffer as ArrayBuffer;
}
