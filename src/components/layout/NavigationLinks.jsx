"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navigation = [
  { label: "Home", href: "/" },
  { label: "Explore Map", href: "/explore" },
  { label: "Rotation Planner", href: "/rotation-planner" },
  { label: "Risk & Uncertainty", href: "/risk-uncertainty" },
  { label: "Data & Method", href: "/data-method" },
];

export default function NavigationLinks({ className, linkClassName, onNavigate }) {
  const pathname = usePathname();

  return (
    <ul className={className}>
      {navigation.map(({ label, href }) => (
        <li key={href}>
          <Link
            href={href}
            aria-current={pathname === href ? "page" : undefined}
            onNavigate={onNavigate}
            className={linkClassName}
          >
            {label}
          </Link>
        </li>
      ))}
    </ul>
  );
}
