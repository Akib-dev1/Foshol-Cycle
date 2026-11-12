"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { ArrowUpRight, Menu, X } from "lucide-react";
import NavigationLinks from "./NavigationLinks";
import { primaryButton } from "./layoutStyles";

export default function MobileMenu() {
  const [open, setOpen] = useState(false);
  const toggleRef = useRef(null);

  function closeMenu() {
    setOpen(false);
    toggleRef.current?.focus();
  }

  function handleKeyDown(event) {
    if (open && event.key === "Escape") {
      event.preventDefault();
      closeMenu();
    }
  }

  return (
    <div className="xl:hidden" onKeyDown={handleKeyDown}>
      <button
        type="button"
        ref={toggleRef}
        aria-controls="mobile-navigation"
        aria-expanded={open}
        aria-label={open ? "Close menu" : "Open menu"}
        onClick={() => setOpen(!open)}
        className="grid size-11 place-items-center rounded-xl border border-line bg-white text-forest hover:bg-mist"
      >
        {open ? <X size={20} aria-hidden="true" /> : <Menu size={20} aria-hidden="true" />}
      </button>
      <nav
        id="mobile-navigation"
        aria-label="Main navigation"
        hidden={!open}
        className="absolute inset-x-0 top-full z-20 mt-2 rounded-2xl border border-line bg-white p-3 shadow-lg"
      >
        <NavigationLinks
          className="space-y-1"
          linkClassName="flex min-h-11 items-center rounded-lg px-3 text-sm font-medium text-muted hover:bg-canvas hover:text-forest aria-[current=page]:bg-mist aria-[current=page]:font-semibold aria-[current=page]:text-forest"
          onNavigate={closeMenu}
        />
        <Link href="/explore" onNavigate={closeMenu} className={`${primaryButton} mt-3 w-full`}>
          Start Exploring <ArrowUpRight size={16} aria-hidden="true" />
        </Link>
      </nav>
    </div>
  );
}
