import { describe, expect, it } from "vitest";
import { buildAccessRequestMailto } from "./SignInPage";

describe("SignInPage", () => {
  it("builds the access request link with a single recipient and cc", () => {
    const href = buildAccessRequestMailto();

    expect(href).toContain("mailto:daniel.cgm@discente.ufma.br?");
    expect(href).toContain("cc=danielgaldez10%40hotmail.com");
    expect(href).not.toContain("mailto:daniel.cgm@discente.ufma.br,");
  });
});
