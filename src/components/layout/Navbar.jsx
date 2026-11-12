import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import Brand from "./Brand";
import MobileMenu from "./MobileMenu";
import NavigationLinks from "./NavigationLinks";
import { container, primaryButton } from "./layoutStyles";

export default function Navbar() {
  return (
    <header className="sticky top-0 z-10 border-b border-line bg-white">
      <a
        href="#main-content"
        className="sr-only rounded-lg bg-white px-4 py-3 text-forest focus:not-sr-only focus:absolute focus:top-2 focus:left-2"
      >
        Skip to content
      </a>
      <div className={`${container} relative flex min-h-[72px] items-center justify-between gap-3`}>
        <Brand />
        <nav aria-label="Main navigation" className="hidden xl:block">
          <NavigationLinks
            className="flex items-center gap-0.5 rounded-xl border border-line bg-canvas p-1 2xl:gap-1.5"
            linkClassName="block whitespace-nowrap rounded-lg px-3 py-2.5 text-[13px] font-medium text-muted hover:bg-white hover:text-forest aria-[current=page]:bg-mist aria-[current=page]:font-semibold aria-[current=page]:text-forest"
          />
        </nav>
        <div className="hidden shrink-0 xl:block">
          <Link href="/explore" className={primaryButton}>
            Start Exploring <ArrowUpRight size={16} aria-hidden="true" />
          </Link>
        </div>
        <MobileMenu />
      </div>
    </header>
  );
}
