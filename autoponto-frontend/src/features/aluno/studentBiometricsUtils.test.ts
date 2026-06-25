import { describe, expect, it } from "vitest";
import { BIOMETRIC_MAX_FILE_BYTES, BIOMETRIC_MAX_FILES, validateBiometricFiles } from "./studentBiometricsUtils";

function file(name: string, type: string, size: number): File {
  return { name, type, size, lastModified: 1 } as File;
}

describe("validateBiometricFiles", () => {
  it("accepts up to five supported images under 5 MB each", () => {
    expect(validateBiometricFiles([
      file("foto-1.jpg", "image/jpeg", 1200),
      file("foto-2.png", "image/png", BIOMETRIC_MAX_FILE_BYTES),
      file("foto-3.webp", "image/webp", 4200),
    ])).toBeNull();
  });

  it("rejects empty, oversized, unsupported or excessive selections", () => {
    expect(validateBiometricFiles([])).toContain("Selecione");
    expect(validateBiometricFiles([file("foto.gif", "image/gif", 1200)])).toContain("JPEG");
    expect(validateBiometricFiles([file("foto.jpg", "image/jpeg", BIOMETRIC_MAX_FILE_BYTES + 1)])).toContain("5 MB");
    expect(validateBiometricFiles(
      Array.from({ length: BIOMETRIC_MAX_FILES + 1 }, (_, index) =>
        file(`foto-${index}.jpg`, "image/jpeg", 1200),
      ),
    )).toContain("no máximo");
  });
});
