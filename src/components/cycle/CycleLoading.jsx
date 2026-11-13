import { HistoricalGrid, panel } from "./CycleLayout";
import LoadingStatus from "./LoadingStatus";

function Placeholder({ className }) {
  return <div className={`rounded-md bg-mist ${className}`} />;
}

function PickerSkeleton() {
  return (
    <div className={`${panel} space-y-3`}>
      <Placeholder className="h-5 w-40 max-w-full" />
      <div className="grid items-start gap-4 md:grid-cols-2">
        <div className="space-y-1.5">
          <Placeholder className="h-3.5 w-20" />
          <Placeholder className="h-11 w-full" />
        </div>
        <Placeholder className="h-4 w-3/4 md:mt-2" />
      </div>
    </div>
  );
}

function RotationSkeleton() {
  return (
    <div className="space-y-4">
      <Placeholder className="h-7 w-44 max-w-full" />
      <div className="rounded-xl border border-line bg-white p-3 sm:p-4">
        <Placeholder className="h-11 w-full md:max-w-72" />
      </div>
      <div className="space-y-2 rounded-2xl border border-line bg-mist/50 p-2 sm:p-3">
        {[0, 1].map((row) => (
          <div key={row} className="grid min-w-0 items-center gap-3 rounded-xl border border-line bg-white p-3 lg:grid-cols-[minmax(0,1fr)_9.5rem]">
            <div className="space-y-2">
              <Placeholder className="h-3 w-24" />
              <div className="grid grid-cols-3 gap-2">
                {[0, 1, 2].map((crop) => <Placeholder key={crop} className="h-12" />)}
              </div>
              <Placeholder className="h-3 w-2/3" />
            </div>
            <Placeholder className="h-11 w-full sm:w-36 lg:w-full" />
          </div>
        ))}
      </div>
    </div>
  );
}

function HistorySkeleton({ count }) {
  return (
    <>
      <div className="rounded-xl border border-line bg-white p-4">
        <Placeholder className="h-4 w-3/4 max-w-96" />
      </div>
      <HistoricalGrid count={count}>
        {Array.from({ length: count }, (_, index) => (
          <div key={index} className={`${panel} space-y-3`}>
            <Placeholder className="h-5 w-24 rounded-full" />
            <Placeholder className="h-5 w-2/3" />
            {[0, 1].map((range) => (
              <div key={range} className="space-y-3 rounded-xl bg-canvas p-3">
                <Placeholder className="h-3.5 w-2/3" />
                <Placeholder className="h-2 w-full rounded-full" />
                <Placeholder className="h-3 w-1/2" />
              </div>
            ))}
          </div>
        ))}
      </HistoricalGrid>
    </>
  );
}

export default function CycleLoading({ message, variant, route = false, count = 1 }) {
  return (
    <div className="min-w-0 space-y-3">
      <LoadingStatus message={message} />
      <div aria-busy="true" aria-label={message} role="region">
        <div aria-hidden="true" className="space-y-4 motion-safe:animate-pulse">
          {route && (
            <div className={`${panel} space-y-3`}>
              <Placeholder className="h-6 w-48 max-w-full" />
              <Placeholder className="h-4 w-3/4 max-w-80" />
              {variant === "picker" && (
                <div className="grid gap-4 md:grid-cols-2">
                  <Placeholder className="h-11" />
                  <Placeholder className="h-11" />
                </div>
              )}
            </div>
          )}
          {variant === "picker" && <PickerSkeleton />}
          {variant === "rotations" && <RotationSkeleton />}
          {variant === "history" && <HistorySkeleton count={count} />}
        </div>
      </div>
    </div>
  );
}
