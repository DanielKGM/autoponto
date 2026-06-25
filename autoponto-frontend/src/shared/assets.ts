export function publicAssetPath(path: string): string {
  const base = import.meta.env.BASE_URL.replace(/\/+$/, "");
  const asset = path.replace(/^\/+/, "");
  return base ? `${base}/${asset}` : `/${asset}`;
}
