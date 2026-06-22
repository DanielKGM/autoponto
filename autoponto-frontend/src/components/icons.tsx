import type { ReactNode, SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

function iconPath(props: IconProps, children: ReactNode) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>
      {children}
    </svg>
  );
}

export function MenuIcon(props: IconProps) {
  return iconPath(props, <><path d="M4 7h16" /><path d="M4 12h16" /><path d="M4 17h10" /></>);
}

export function CloseIcon(props: IconProps) {
  return iconPath(props, <><path d="M6 6l12 12" /><path d="M18 6L6 18" /></>);
}

export function ChevronDownIcon(props: IconProps) {
  return iconPath(props, <path d="M6 9l6 6 6-6" />);
}

export function UserIcon(props: IconProps) {
  return iconPath(props, <><path d="M20 21a8 8 0 0 0-16 0" /><circle cx="12" cy="7" r="4" /></>);
}

export function LogOutIcon(props: IconProps) {
  return iconPath(props, <><path d="M10 17l5-5-5-5" /><path d="M15 12H3" /><path d="M21 4v16" /></>);
}

export function LockIcon(props: IconProps) {
  return iconPath(props, <><rect x="4" y="10" width="16" height="10" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></>);
}

export function GraduationIcon(props: IconProps) {
  return iconPath(props, <><path d="M22 10L12 5 2 10l10 5 10-5Z" /><path d="M6 12v5c3 2 9 2 12 0v-5" /></>);
}

export function TeacherIcon(props: IconProps) {
  return iconPath(props, <><path d="M4 5h16v10H4z" /><path d="M8 21l4-6 4 6" /><path d="M12 15v6" /></>);
}

export function AdminIcon(props: IconProps) {
  return iconPath(props, <><path d="M12 3l7 4v5c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V7l7-4Z" /><path d="M9 12l2 2 4-5" /></>);
}

export function MapIcon(props: IconProps) {
  return iconPath(props, <><path d="M9 18l-6 3V6l6-3 6 3 6-3v15l-6 3-6-3Z" /><path d="M9 3v15" /><path d="M15 6v15" /></>);
}

export function SunIcon(props: IconProps) {
  return iconPath(props, <><circle cx="12" cy="12" r="4" /><path d="M12 2v2" /><path d="M12 20v2" /><path d="M4.93 4.93l1.41 1.41" /><path d="M17.66 17.66l1.41 1.41" /><path d="M2 12h2" /><path d="M20 12h2" /><path d="M4.93 19.07l1.41-1.41" /><path d="M17.66 6.34l1.41-1.41" /></>);
}

export function MoonIcon(props: IconProps) {
  return iconPath(props, <path d="M21 12.8A8.5 8.5 0 1 1 11.2 3 6.8 6.8 0 0 0 21 12.8Z" />);
}

export function PinIcon(props: IconProps) {
  return iconPath(props, <><path d="M12 21s7-4.6 7-11a7 7 0 1 0-14 0c0 6.4 7 11 7 11Z" /><circle cx="12" cy="10" r="2.5" /></>);
}
