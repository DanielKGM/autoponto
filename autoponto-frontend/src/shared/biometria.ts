export const MAX_CAPTURAS_BIOMETRIA = 5;
export const MAX_BYTES_BIOMETRIA = 2 * 1024 * 1024;

export async function arquivoParaBase64(arquivo: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const resultado = String(reader.result || "");
      resolve(resultado.includes(",") ? resultado.split(",")[1] : resultado);
    };
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(arquivo);
  });
}

export function validarArquivosBiometria(arquivos: File[]): string | null {
  if (arquivos.length === 0) return "Selecione ao menos uma imagem.";
  if (arquivos.length > MAX_CAPTURAS_BIOMETRIA) return `Selecione no maximo ${MAX_CAPTURAS_BIOMETRIA} imagens.`;
  if (arquivos.some((arquivo) => !arquivo.type.startsWith("image/"))) return "Use apenas arquivos de imagem.";
  if (arquivos.some((arquivo) => arquivo.size > MAX_BYTES_BIOMETRIA)) return "Cada imagem deve ter no maximo 2 MB.";
  return null;
}
