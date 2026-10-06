import {
  HiOutlineMapPin,
  HiOutlineCalendarDays,
  HiOutlineScale,
} from "react-icons/hi2";

const MethodologySection = () => {
  return (
    <section className="bg-[#f3f0e8] py-14 sm:py-16 lg:py-20">
      <div className="max-w-9/12 mx-auto max-lg:max-w-10/12 max-md:max-w-11/12">
        {/* SECTION HEADING */}
        <div className="mb-10 max-w-4xl lg:mb-12">
          <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.22em] text-[#216244]">
            Methodology
          </p>

          <h2 className="text-3xl font-semibold tracking-tight text-[#0d281d] sm:text-[34px]">
            Plan around the season you have.
          </h2>

          <p className="mt-3 max-w-4xl text-[15px] leading-7 text-[#4e5652] sm:text-base">
            Empirical decision modeling that integrates historical
            meteorological observations with agronomic duration ranges to
            evaluate sequential crop compatibility.
          </p>
        </div>

        {/* CARDS */}
        <div className="grid gap-5 md:grid-cols-3 lg:gap-7">
          {/* CARD 1 */}
          <div className="flex min-h-66.25 flex-col border border-[#eeece5] bg-white p-6 transition duration-200 hover:border-[#d8ddd8] sm:p-7">
            <div className="mb-6 flex items-start justify-between">
              <span className="font-mono text-xs font-semibold text-[#26704b]">
                01
              </span>

              <HiOutlineMapPin className="text-xl text-[#bdc7c1]" />
            </div>

            <h3 className="text-xl font-semibold tracking-[-0.015em] text-[#112a20]">
              Tell us about your field
            </h3>

            <p className="mt-3 text-sm leading-6 text-[#555e59]">
              Add your upazila location, soil drainage profile, current crop
              variety, and planned rotation intent for the upcoming harvest
              cycle.
            </p>

            <div className="mt-auto border-t border-[#e4e6e2] pt-4">
              <p className="text-[9px] font-bold uppercase tracking-[0.18em] text-[#737d77]">
                Input stage · 2 min
              </p>
            </div>
          </div>

          {/* CARD 2 */}
          <div className="flex min-h-66.25 flex-col border border-[#eeece5] bg-white p-6 transition duration-200 hover:border-[#d8ddd8] sm:p-7">
            <div className="mb-6 flex items-start justify-between">
              <span className="font-mono text-xs font-semibold text-[#26704b]">
                02
              </span>

              <HiOutlineCalendarDays className="text-xl text-[#bdc7c1]" />
            </div>

            <h3 className="text-xl font-semibold tracking-[-0.015em] text-[#112a20]">
              Check the planting window
            </h3>

            <p className="mt-3 text-sm leading-6 text-[#555e59]">
              Simulate harvest timing under standard vs. late monsoons to assess
              when fields will reach workable moisture levels for replanting.
            </p>

            <div className="mt-auto border-t border-[#e4e6e2] pt-4">
              <p className="text-[9px] font-bold uppercase tracking-[0.18em] text-[#737d77]">
                Simulation engine · instant
              </p>
            </div>
          </div>

          {/* CARD 3 */}
          <div className="flex min-h-66.25 flex-col border border-[#eeece5] bg-white p-6 transition duration-200 hover:border-[#d8ddd8] sm:p-7">
            <div className="mb-6 flex items-start justify-between">
              <span className="font-mono text-xs font-semibold text-[#26704b]">
                03
              </span>

              <HiOutlineScale className="text-xl text-[#bdc7c1]" />
            </div>

            <h3 className="text-xl font-semibold tracking-[-0.015em] text-[#112a20]">
              Compare your options
            </h3>

            <p className="mt-3 text-sm leading-6 text-[#555e59]">
              Explore short-duration alternative varieties such as Tori-7 vs.
              BARI Sarisha-14 or resilient later crops when nominal windows
              narrow.
            </p>

            <div className="mt-auto border-t border-[#e4e6e2] pt-4">
              <p className="text-[9px] font-bold uppercase tracking-[0.18em] text-[#737d77]">
                Decision matrix · optimized
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default MethodologySection;
