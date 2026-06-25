import type { ReactNode, SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

function iconPath(props: IconProps, children: ReactNode) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      {children}
    </svg>
  );
}

export function MenuIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <path d="M4 7h16" />
      <path d="M4 12h16" />
      <path d="M4 17h10" />
    </>,
  );
}

export function CloseIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <path d="M6 6l12 12" />
      <path d="M18 6L6 18" />
    </>,
  );
}

export function ChevronDownIcon(props: IconProps) {
  return iconPath(props, <path d="M6 9l6 6 6-6" />);
}

export function ChevronRightIcon(props: IconProps) {
  return iconPath(props, <path d="M9 6l6 6-6 6" />);
}

export function ChevronUpIcon(props: IconProps) {
  return iconPath(props, <path d="M6 15l6-6 6 6" />);
}

export function RefreshIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <path d="M20 6v5h-5" />
      <path d="M4 18v-5h5" />
      <path d="M6.5 9a7 7 0 0 1 11.8-2.5L20 11" />
      <path d="M4 13l1.7 4.5A7 7 0 0 0 17.5 15" />
    </>,
  );
}

export function PlusIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <path d="M12 5v14" />
      <path d="M5 12h14" />
    </>,
  );
}

export function EditIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5Z" />
    </>,
  );
}

export function TrashIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <path d="M3 6h18" />
      <path d="M8 6V4h8v2" />
      <path d="M6 6l1 14h10l1-14" />
      <path d="M10 11v5" />
      <path d="M14 11v5" />
    </>,
  );
}

export function CopyIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <rect x="8" y="8" width="12" height="12" rx="2" />
      <path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2" />
    </>,
  );
}

export function UploadIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <path d="M12 16V4" />
      <path d="M7 9l5-5 5 5" />
      <path d="M20 16v3a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-3" />
    </>,
  );
}

export function UsersIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <circle cx="9" cy="8" r="4" />
      <circle cx="17" cy="9" r="3" />
      <path d="M2 20c0-3.9 3.1-7 7-7s7 3.1 7 7" />
      <path d="M22 20c0-2.5-2-5-5-5" />
    </>,
  );
}

export function UserCheckIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <circle cx="9" cy="8" r="4" />
      <path d="M2 20c0-3.9 3.1-7 7-7s7 3.1 7 7" />
      <path d="M16 10l2 2 4-4" />
    </>,
  );
}

export function UserXIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <circle cx="9" cy="8" r="4" />
      <path d="M2 20c0-3.9 3.1-7 7-7s7 3.1 7 7" />
      <path d="M17 8l5 5" />
      <path d="M22 8l-5 5" />
    </>,
  );
}

export function ShieldUserIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <path d="M12 2l9 4v6c0 5-4 9-9 10-5-1-9-5-9-10V6z" />
      <circle cx="12" cy="11" r="2.5" />
      <path d="M8 17a4 4 0 0 1 8 0" />
    </>,
  );
}

export function DatabaseIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <ellipse cx="12" cy="5" rx="9" ry="3" />
      <path d="M3 5v6c0 1.7 4 3 9 3s9-1.3 9-3V5" />
      <path d="M3 11v6c0 1.7 4 3 9 3s9-1.3 9-3v-6" />
    </>,
  );
}

export function ChartIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <path d="M4 19V5" />
      <path d="M8 19v-8" />
      <path d="M12 19V9" />
      <path d="M16 19v-5" />
      <path d="M20 19v-9" />
    </>,
  );
}

export function CheckCircleIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <circle cx="12" cy="12" r="10" />
      <path d="M8 12l3 3 5-7" />
    </>,
  );
}

export function InfoIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <circle cx="12" cy="12" r="10" />
      <path d="M12 11v5" />
      <path d="M12 8v.01" />
    </>,
  );
}

export function HelpIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <circle cx="12" cy="12" r="10" />
      <path d="M9.5 9a2.8 2.8 0 0 1 5 1.7c0 1.9-2.5 2.2-2.5 4" />
      <path d="M12 18v.01" />
    </>,
  );
}

export function HeadphonesIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <path d="M3 14v-2a9 9 0 0 1 18 0v2" />
      <path d="M5 14h3v6H5a2 2 0 0 1-2-2v-2a2 2 0 0 1 2-2Z" />
      <path d="M19 14h-3v6h3a2 2 0 0 0 2-2v-2a2 2 0 0 0-2-2Z" />
    </>,
  );
}

export function ClockIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </>,
  );
}

export function EyeIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </>,
  );
}

export function UnlockIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <rect x="4" y="11" width="16" height="11" rx="2" />
      <path d="M8 11V7a4 4 0 0 1 7.5-2" />
    </>,
  );
}

export function CameraIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
      <circle cx="12" cy="13" r="4" />
    </>,
  );
}

export function TargetIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="12" r="6" />
      <circle cx="12" cy="12" r="2" />
    </>,
  );
}

export function ShieldIcon(props: IconProps) {
  return iconPath(props, <path d="M12 2l9 4v6c0 5-4 9-9 10-5-1-9-5-9-10V6z" />);
}

export function MaximizeIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <path d="M8 3H3v5" />
      <path d="M16 3h5v5" />
      <path d="M21 16v5h-5" />
      <path d="M8 21H3v-5" />
      <path d="M3 3l6 6" />
      <path d="M21 3l-6 6" />
      <path d="M21 21l-6-6" />
      <path d="M3 21l6-6" />
    </>,
  );
}

export function MinimizeIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <path d="M9 3v6H3" />
      <path d="M15 3v6h6" />
      <path d="M15 21v-6h6" />
      <path d="M9 21v-6H3" />
    </>,
  );
}

export function MemoryIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <rect x="6" y="6" width="12" height="12" rx="2" />
      <path d="M9 2v4" />
      <path d="M15 2v4" />
      <path d="M9 18v4" />
      <path d="M15 18v4" />
      <path d="M2 9h4" />
      <path d="M2 15h4" />
      <path d="M18 9h4" />
      <path d="M18 15h4" />
    </>,
  );
}

export function SignalIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <path d="M2 20h.01" />
      <path d="M7 20v-4" />
      <path d="M12 20v-8" />
      <path d="M17 20V8" />
      <path d="M22 20V4" />
    </>,
  );
}

export function ActivityIcon(props: IconProps) {
  return iconPath(props, <path d="M3 12h4l3-7 4 14 3-7h4" />);
}

export function NoDataIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <path d="M6 6l12 12" />
      <path d="M18 6L6 18" />
    </>,
  );
}

export function UserIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <path d="M20 21a8 8 0 0 0-16 0" />
      <circle cx="12" cy="7" r="4" />
    </>,
  );
}

export function LogOutIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <path d="M10 17l5-5-5-5" />
      <path d="M15 12H3" />
      <path d="M21 4v16" />
    </>,
  );
}

export function LockIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <rect x="4" y="10" width="16" height="10" rx="2" />
      <path d="M8 10V7a4 4 0 0 1 8 0v3" />
    </>,
  );
}

export function GraduationIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <path d="M22 10L12 5 2 10l10 5 10-5Z" />
      <path d="M6 12v5c3 2 9 2 12 0v-5" />
    </>,
  );
}

export function CalendarIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <rect x="3" y="4" width="18" height="17" rx="2" />
      <path d="M8 2v5" />
      <path d="M16 2v5" />
      <path d="M3 10h18" />
    </>,
  );
}

export function TeacherIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <path d="M4 5h16v10H4z" />
      <path d="M8 21l4-6 4 6" />
      <path d="M12 15v6" />
    </>,
  );
}

export function AdminIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <path d="M12 3l7 4v5c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V7l7-4Z" />
      <path d="M9 12l2 2 4-5" />
    </>,
  );
}

export function MapIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <path d="M9 18l-6 3V6l6-3 6 3 6-3v15l-6 3-6-3Z" />
      <path d="M9 3v15" />
      <path d="M15 6v15" />
    </>,
  );
}

export function GitHubIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true" {...props}>
      <path d="M8 0a8 8 0 0 0-2.53 15.59c.4.07.55-.17.55-.38v-1.34c-2.23.48-2.69-1.07-2.69-1.07-.36-.92-.89-1.16-.89-1.16-.73-.5.05-.49.05-.49.8.06 1.23.83 1.23.83.71 1.23 1.87.87 2.33.67.07-.52.28-.87.5-1.07-1.78-.2-3.64-.89-3.64-3.96 0-.87.31-1.59.83-2.15-.08-.2-.36-1.02.08-2.13 0 0 .67-.21 2.2.82a7.66 7.66 0 0 1 4 0c1.53-1.03 2.2-.82 2.2-.82.44 1.11.16 1.93.08 2.13.51.56.83 1.28.83 2.15 0 3.07-1.87 3.76-3.65 3.95.29.25.54.74.54 1.5v2.22c0 .21.14.46.55.38A8 8 0 0 0 8 0Z" />
    </svg>
  );
}

export function SunIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2" />
      <path d="M12 20v2" />
      <path d="M4.93 4.93l1.41 1.41" />
      <path d="M17.66 17.66l1.41 1.41" />
      <path d="M2 12h2" />
      <path d="M20 12h2" />
      <path d="M4.93 19.07l1.41-1.41" />
      <path d="M17.66 6.34l1.41-1.41" />
    </>,
  );
}

export function MoonIcon(props: IconProps) {
  return iconPath(
    props,
    <path d="M21 12.8A8.5 8.5 0 1 1 11.2 3 6.8 6.8 0 0 0 21 12.8Z" />,
  );
}

export function PinIcon(props: IconProps) {
  return iconPath(
    props,
    <>
      <path d="M12 21s7-4.6 7-11a7 7 0 1 0-14 0c0 6.4 7 11 7 11Z" />
      <circle cx="12" cy="10" r="2.5" />
    </>,
  );
}
