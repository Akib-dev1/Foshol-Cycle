import { FiArrowRight, FiAlertTriangle, FiInfo } from "react-icons/fi";

const HeroSection = () => {
  return (
    <section className="bg-[#fbfaf7] py-12 sm:py-16 lg:py-24">
      <div className="max-w-9/12 mx-auto max-lg:max-w-10/12 max-md:max-w-11/12">
        <div className="grid items-center gap-12 lg:grid-cols-[0.82fr_1.18fr] lg:gap-16 xl:gap-20">
          {/* LEFT SIDE */}
          <div className="max-w-xl">
            <p className="mb-4 text-[10px] font-bold uppercase tracking-[0.22em] text-[#1f4937]">
              Crop rotation, with timing in mind
            </p>

            <h1 className="max-w-140 text-4xl font-semibold leading-[1.12] tracking-[-0.035em] text-[#08291d] sm:text-5xl lg:text-[52px]">
              Will your next crop still fit this season?
            </h1>

            <p className="mt-6 max-w-137.5 text-[15px] leading-7 text-[#48534e] sm:text-[17px] sm:leading-8">
              A late harvest can leave little time for the next crop. Check your
              rotation against changing seasons using NASA climate history and
              local agricultural data.
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-5 sm:gap-7">
              <button className="cursor-pointer bg-[#063c2a] px-6 py-3.5 text-sm font-semibold text-white transition duration-200 hover:bg-[#0b5039]">
                Check my rotation
              </button>

              <button className="group flex cursor-pointer items-center gap-2 text-sm font-semibold text-[#172b22]">
                Explore a sample
                <FiArrowRight className="text-base transition-transform duration-200 group-hover:translate-x-1" />
              </button>
            </div>
          </div>

          {/* RIGHT SIDE */}
          <div className="w-full border border-[#e5e6e1] bg-white p-5 shadow-[0_1px_4px_rgba(0,0,0,0.025)] sm:p-7">
            {/* Header */}
            <div className="flex items-start justify-between gap-5 border-b border-[#dfe4e0] pb-5">
              <div>
                <h2 className="text-lg font-semibold text-[#10291f] sm:text-xl">
                  One delay can change the next season.
                </h2>

                <p className="mt-1 text-xs text-[#66706b]">
                  Timing alignment across crop transition windows
                </p>
              </div>

              <span className="hidden shrink-0 pt-1 text-[9px] font-bold uppercase tracking-[0.2em] text-[#263c31] sm:block">
                Phenological track
              </span>
            </div>

            {/* PLAN A */}
            <div className="mt-6">
              <div className="mb-2 flex items-center justify-between gap-3">
                <span className="text-[9px] font-bold uppercase tracking-[0.13em] text-[#34483e]">
                  Plan A · Nominal timeline
                </span>

                <span className="text-right text-[9px] font-bold tracking-[0.08em] text-[#27714c]">
                  18 Days Optimal Gap
                </span>
              </div>

              <div className="flex h-12 gap-1.5 sm:gap-2">
                <div className="flex min-w-0 flex-[2.5] items-center justify-between bg-[#2d7355] px-2 sm:px-3 text-white">
                  <span className="truncate text-[9px] font-semibold sm:text-xs">
                    Aman Rice (Current)
                  </span>

                  <span className="ml-2 hidden whitespace-nowrap text-[8px] font-bold tracking-[0.08em] sm:inline">
                    Harvest: Nov 15
                  </span>
                </div>

                <div className="flex flex-[0.85] items-center justify-center bg-[#e7e8eb] px-1 text-center text-[8px] font-bold text-[#41464a] sm:px-2 sm:text-[9px]">
                  Field Prep
                </div>

                <div className="flex min-w-0 flex-[1.85] items-center justify-between bg-[#438766] px-2 sm:px-3 text-white">
                  <span className="truncate text-[9px] font-semibold sm:text-xs">
                    Mustard Window
                  </span>

                  <span className="ml-2 hidden text-[8px] font-bold uppercase tracking-widest sm:inline">
                    Optimal
                  </span>
                </div>
              </div>
            </div>

            {/* PLAN B */}
            <div className="mt-8">
              <div className="mb-2 flex items-center justify-between gap-3">
                <span className="text-[9px] font-bold uppercase tracking-[0.12em] text-[#9d3e28]">
                  Plan B · Extended monsoon shift
                </span>

                <span className="text-right text-[9px] font-bold tracking-[0.08em] text-[#c33f2f]">
                  +14 Days Incurred
                </span>
              </div>

              <div className="flex h-12 gap-1.5 sm:gap-2">
                <div className="flex min-w-0 flex-[3.2] items-center justify-between bg-[#2d7355] px-2 sm:px-3 text-white">
                  <span className="truncate text-[9px] font-semibold sm:text-xs">
                    Aman Rice (Current)
                  </span>

                  <span className="ml-2 hidden whitespace-nowrap bg-[#153d2d] px-2 py-1 text-[8px] font-bold sm:inline">
                    DELAYED +14D
                  </span>
                </div>

                <div className="flex flex-[0.85] items-center justify-center bg-[#e7e8eb] px-1 text-center text-[8px] font-bold text-[#41464a] sm:px-2 sm:text-[9px]">
                  Field Prep
                </div>

                <div className="flex min-w-0 flex-[1.35] items-center gap-1.5 bg-[#fde0d1] px-2 text-[#6d2f21] sm:px-3">
                  <FiAlertTriangle className="shrink-0 text-sm" />

                  <span className="truncate text-[8px] font-bold sm:text-[10px]">
                    Narrow Window
                  </span>

                  <span className="ml-auto hidden text-[8px] font-semibold sm:block">
                    -52%
                  </span>
                </div>
              </div>

              {/* Warning */}
              <div className="mt-2 flex items-start gap-2 bg-[#faf7ef] px-3 py-3 text-[10px] leading-5 text-[#515650] sm:text-[11px]">
                <FiInfo className="mt-0.5 shrink-0 text-[15px] text-[#7d3c25]" />

                <p>
                  <span className="font-semibold text-[#344139]">
                    Window compression:
                  </span>{" "}
                  Sowing mustard past late November reduces canopy yield by up
                  to 35% in northern zones due to terminal heat stress during
                  pod filling.
                </p>
              </div>
            </div>

            {/* Legend */}
            <div className="mt-6 flex flex-wrap items-center gap-x-5 gap-y-3 border-t border-[#e0e4e1] pt-5">
              <div className="flex items-center gap-2">
                <span className="h-3 w-3 bg-[#2d7355]" />
                <span className="text-[9px] font-bold tracking-[0.08em] text-[#445149]">
                  Standing Crop
                </span>
              </div>

              <div className="flex items-center gap-2">
                <span className="h-3 w-3 bg-[#e7e8eb]" />
                <span className="text-[9px] font-bold tracking-[0.08em] text-[#445149]">
                  Tillage / Rest
                </span>
              </div>

              <div className="flex items-center gap-2">
                <span className="h-3 w-3 bg-[#438766]" />
                <span className="text-[9px] font-bold tracking-[0.08em] text-[#445149]">
                  Viable Window
                </span>
              </div>

              <span className="ml-auto hidden text-[10px] italic text-[#929792] lg:inline">
                Illustrative transition model
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
