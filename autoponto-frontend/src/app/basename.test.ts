import { describe, expect, it } from "vitest";
import { normalizarBasename } from "./basename";

describe("router basename", () => {
  it("keeps the root base path unchanged", () => {
    expect(normalizarBasename("/")).toBe("/");
  });

  it("normalizes the production base path for React Router", () => {
    expect(normalizarBasename("/interscity_lh/catalog/autoponto/")).toBe(
      "/interscity_lh/catalog/autoponto",
    );
  });

  it("adds the initial slash when it is missing", () => {
    expect(normalizarBasename("interscity_lh/catalog/autoponto/")).toBe(
      "/interscity_lh/catalog/autoponto",
    );
  });
});
