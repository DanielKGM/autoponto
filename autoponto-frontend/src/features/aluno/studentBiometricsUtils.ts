export const BIOMETRIC_MAX_FILES = 5;
export const BIOMETRIC_MAX_FILE_BYTES = 5 * 1024 * 1024;

export type BiometricInstructionIcon = "user" | "sun" | "eye" | "headphones";

export type BiometricInstruction = {
  title: string;
  text: string;
  icon: BiometricInstructionIcon;
};

export const BIOMETRIC_INSTRUCTIONS: BiometricInstruction[] = [
  {
    title: "Rosto centralizado",
    text: "Mantenha o rosto inteiro visível, olhando para a câmera.",
    icon: "user",
  },
  {
    title: "Boa iluminação",
    text: "Use luz frontal e evite sombras fortes no rosto.",
    icon: "sun",
  },
  {
    title: "Imagem nítida",
    text: "Evite fotos tremidas, desfocadas ou com baixa resolução.",
    icon: "eye",
  },
  {
    title: "Pouca obstrução",
    text: "Retire objetos que cubram olhos, boca ou contorno do rosto.",
    icon: "headphones",
  },
];

const ACCEPTED_IMAGE_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);

export function formatBiometricFileSize(bytes: number) {
  if (bytes >= 1024 * 1024) {
    if (bytes % (1024 * 1024) === 0) {
      return `${bytes / (1024 * 1024)} MB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
  return `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

export function validateBiometricFiles(files: File[]): string | null {
  if (files.length === 0) {
    return "Selecione ao menos uma imagem para cadastrar a biometria.";
  }
  if (files.length > BIOMETRIC_MAX_FILES) {
    return `Selecione no máximo ${BIOMETRIC_MAX_FILES} fotos.`;
  }

  const invalidType = files.find((file) => !ACCEPTED_IMAGE_TYPES.has(file.type));
  if (invalidType) {
    return "Use apenas imagens JPEG, PNG ou WebP.";
  }

  const oversized = files.find((file) => file.size > BIOMETRIC_MAX_FILE_BYTES);
  if (oversized) {
    return `Cada foto deve ter no máximo ${formatBiometricFileSize(BIOMETRIC_MAX_FILE_BYTES)}.`;
  }

  return null;
}
