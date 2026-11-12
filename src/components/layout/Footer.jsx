import Brand from "./Brand";
import NavigationLinks from "./NavigationLinks";
import { container } from "./layoutStyles";

export default function Footer() {
  return (
    <footer className="border-t border-line bg-white">
      <div className={`${container} py-9 sm:py-11`}>
        <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-center">
          <Brand />
          <nav aria-label="Footer navigation">
            <NavigationLinks
              className="flex flex-wrap gap-x-5 gap-y-2 text-sm font-medium"
              linkClassName="inline-flex min-h-9 items-center rounded text-muted hover:text-forest aria-[current=page]:text-forest"
            />
          </nav>
        </div>
        <div className="mt-6 flex flex-col justify-between gap-2 border-t border-line pt-5 text-xs leading-relaxed text-muted lg:flex-row lg:gap-6">
          <p>
            The map shows sample data. The Rajshahi pilot uses historical{" "}
            <a className="rounded font-medium text-leaf underline underline-offset-3" href="https://power.larc.nasa.gov/docs/methodology/communities/">
              NASA POWER
            </a>.
          </p>
          <p>
            Photograph by{" "}
            <a className="rounded font-medium text-leaf underline underline-offset-3" href="https://unsplash.com/photos/overhead-view-of-lush-green-fields-and-blue-skies-Rw1TIYk3vNg">
              Abdullah Al Mamun on Unsplash
            </a>.
          </p>
        </div>
      </div>
    </footer>
  );
}
