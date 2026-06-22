import { publicAssetPath } from "../../app/assets";

type BrandLogoProps = {
  className?: string;
  iconClassName?: string;
  textClassName?: string;
  iconOnly?: boolean;
  size?: "sm" | "md" | "lg" | "xl";
  tone?: "default" | "onDark";
};

function cx(...classes: Array<string | undefined | false>) {
  return classes.filter(Boolean).join(" ");
}

export function BrandLogo({
  className,
  iconClassName,
  textClassName,
  iconOnly = false,
  size = "md",
  tone = "default",
}: BrandLogoProps) {
  return (
    <span
      className={cx(
        "brand-logo",
        `brand-logo-${size}`,
        tone === "onDark" && "brand-logo-on-dark",
        iconOnly && "brand-logo-icon-only",
        className,
      )}
    >
      <img
        src={publicAssetPath("images/icone-logo.svg")}
        alt=""
        aria-hidden="true"
        className={cx("brand-logo-icon", iconClassName)}
      />
      {iconOnly ? (
        <span className="sr-only">AutoPonto</span>
      ) : (
        <span className={cx("brand-logo-text", textClassName)}>
          AutoPonto
        </span>
      )}
    </span>
  );
}
