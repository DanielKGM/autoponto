import { twMerge } from "tailwind-merge";

type BrandLogoProps = {
  className?: string;
  iconClassName?: string;
  textClassName?: string;
  iconOnly?: boolean;
  size?: "sm" | "md" | "lg" | "xl";
  tone?: "default" | "onDark";
};

const sizes = {
  sm: {
    root: "gap-2",
    icon: "h-6 w-6",
    text: "text-xl",
  },
  md: {
    root: "gap-2",
    icon: "h-7 w-7",
    text: "text-2xl",
  },
  lg: {
    root: "gap-2.5",
    icon: "h-8 w-8",
    text: "text-3xl",
  },
  xl: {
    root: "gap-3",
    icon: "h-10 w-10",
    text: "text-4xl",
  },
};

export function BrandLogo({
  className,
  iconClassName,
  textClassName,
  iconOnly = false,
  size = "md",
  tone = "default",
}: BrandLogoProps) {
  const currentSize = sizes[size];
  const textTone =
    tone === "onDark" ? "text-white" : "text-gray-900 dark:text-white";

  return (
    <span
      className={twMerge(
        "inline-flex items-center whitespace-nowrap",
        currentSize.root,
        className,
      )}
    >
      <img
        src="/images/logo/icone-logo.svg"
        alt=""
        aria-hidden="true"
        className={twMerge(
          "shrink-0 object-contain",
          currentSize.icon,
          iconClassName,
        )}
      />
      {iconOnly ? (
        <span className="sr-only">AutoPonto</span>
      ) : (
        <span
          className={twMerge(
            "font-semibold leading-none tracking-normal",
            currentSize.text,
            textTone,
            textClassName,
          )}
        >
          AutoPonto
        </span>
      )}
    </span>
  );
}
