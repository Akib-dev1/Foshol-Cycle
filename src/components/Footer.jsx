import { FiArrowUpRight } from "react-icons/fi";

const Footer = () => {
  return (
    <footer className="border-t border-[#e7e4dc] bg-[#fbfaf7]">
      <div className="max-w-9/12 mx-auto max-lg:max-w-10/12 max-md:max-w-11/12">
        <div className="flex flex-col gap-8 py-10 md:flex-row md:items-end md:justify-between lg:py-12">
          {/* LEFT */}
          <div>
            <h3 className="text-xl font-semibold tracking-[-0.02em] text-[#0d281d]">
              ফসল-Cycle
            </h3>

            <p className="mt-3 max-w-md text-sm leading-6 text-[#68716d]">
              Helping farmers understand whether the next crop still fits the
              season before planting begins.
            </p>
          </div>

          {/* RIGHT */}
          <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:gap-8">
            <button
              type="button"
              className="flex cursor-pointer items-center gap-2 text-sm font-medium text-[#263a31] transition-colors duration-200 hover:text-[#0b5039]"
              onClick={() =>
                window.scrollTo({
                  top: 0,
                  behavior: "smooth",
                })
              }
            >
              Back to top
              <FiArrowUpRight className="text-base" />
            </button>
          </div>
        </div>

        {/* BOTTOM BAR */}
        <div className="flex flex-col gap-3 border-t border-[#ebe8e0] py-5 text-[11px] text-[#7a817d] sm:flex-row sm:items-center sm:justify-between">
          <p>© {new Date().getFullYear()} ফসল-Cycle. All rights reserved.</p>

          <p className="uppercase tracking-[0.14em]">
            Climate-aware crop rotation planning
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
