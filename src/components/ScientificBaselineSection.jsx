import { HiOutlineShieldCheck } from "react-icons/hi2";

const ScientificBaselineSection = () => {
  return (
    <section className="bg-[#fbfaf7] py-12 sm:py-16">
      <div className="max-w-9/12 mx-auto max-lg:max-w-10/12 max-md:max-w-11/12">
        <div className="border border-[#ebe8df] bg-white px-6 py-7 sm:px-8 lg:px-9 lg:py-8">
          <div className="grid gap-8 lg:grid-cols-[0.62fr_1.38fr] lg:gap-16">
            {/* LEFT */}
            <div>
              <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-[#68736d]">
                Scientific baseline
              </p>

              <h2 className="max-w-[320px] text-2xl font-semibold leading-[1.35] tracking-[-0.02em] text-[#0d281d]">
                Climate history meets local crop knowledge.
              </h2>
            </div>

            {/* RIGHT */}
            <div>
              <p className="text-[15px] leading-7 text-[#48514d] sm:text-base">
                NASA POWER provides long-term daily surface solar radiation,
                precipitation, and temperature records over 30+ years. Local
                agricultural extensions (BARI, BRRI) and field agronomy reports
                contextualize these historical baselines for realistic cropping
                patterns.
              </p>

              <div className="mt-5 flex items-start gap-2 border-t border-[#e1e3de] pt-4 text-[11px] leading-5 text-[#5c645f] sm:text-[12px]">
                <HiOutlineShieldCheck className="mt-0.5 shrink-0 text-[18px] text-[#65756c]" />

                <p>
                  <span className="font-semibold text-[#33443b]">
                    Methodology note:
                  </span>{" "}
                  Historical scenarios demonstrate climatic boundaries and
                  risks. They do not constitute weather forecasting services or
                  guarantee specific seasonal yields.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default ScientificBaselineSection;
