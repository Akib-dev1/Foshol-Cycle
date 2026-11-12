const rainfallScale = 400;
const rainfallTicks = [400, 300, 200, 100, 0];

export default function RainfallChart({ monthlyRainfall }) {
  return (
    <figure className="min-w-0 rounded-2xl border border-line bg-white p-4 sm:p-5">
      <figcaption className="text-sm font-semibold text-forest">Monthly rainfall</figcaption>
      <p className="mt-1 text-xs text-muted">Millimeters (mm)</p>
      <div aria-hidden="true" className="mt-5 grid grid-cols-[auto_minmax(0,1fr)] gap-x-2 sm:gap-x-3">
        <div className="flex h-32 flex-col justify-between text-right text-[10px] leading-none text-muted">
          {rainfallTicks.map((tick) => <span key={tick}>{tick}</span>)}
        </div>
        <div className="relative">
          <div className="absolute inset-x-0 top-0 flex h-32 flex-col justify-between">
            {rainfallTicks.map((tick) => <span key={tick} className="border-t border-dashed border-line" />)}
          </div>
          <div className="relative grid grid-cols-12 gap-1 sm:gap-1.5">
            {monthlyRainfall.map(({ month, millimeters }, index) => (
              <div key={month} className="min-w-0 text-center">
                <div className="flex h-32 items-end">
                  <div
                    className={`w-full rounded-t-sm ${month === "Jul" ? "bg-[#337aa8]" : "bg-[#85b7d8]"}`}
                    style={{ height: `${millimeters / rainfallScale * 100}%` }}
                  />
                </div>
                <span className={`${index % 2 ? "invisible sm:visible" : ""} mt-2 block text-[9px] font-medium leading-none text-muted`}>
                  {month}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
      <ul className="sr-only">
        {monthlyRainfall.map(({ month, millimeters }) => (
          <li key={month}>{month} {millimeters} mm</li>
        ))}
      </ul>
    </figure>
  );
}
