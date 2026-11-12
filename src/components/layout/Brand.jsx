import Link from "next/link";
import { Sprout } from "lucide-react";

export default function Brand() {
  return (
    <Link href="/" className="inline-flex w-fit items-center gap-2.5 rounded-lg text-forest">
      <span className="grid size-9 place-items-center rounded-xl bg-forest text-mist">
        <Sprout size={20} aria-hidden="true" />
      </span>
      <span className="text-lg font-bold tracking-[-0.045em]">FosholCycle</span>
    </Link>
  );
}
