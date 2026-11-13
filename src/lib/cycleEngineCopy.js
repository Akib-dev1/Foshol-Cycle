import { formatDate } from "./cycleAlgo.js";

const water = {
  WATER_DEMAND_EVIDENCE_MISSING: ["The crop profile has no quantified water-demand evidence (an FAO range or a local phase water total), so water fit stays unknown even when irrigation is reported available.", "ফসলটির পানির চাহিদার পরিমাণ সম্পর্কে FAO-এর পরিসর বা স্থানীয় চাষপর্যায়ের মোট পানির তথ্য নেই। তাই সেচের ব্যবস্থা থাকলেও পানির উপযোগিতা জানা যায় না।"],
  WATER_DEMAND_EVIDENCE_INVALID: ["The crop profile has a negative water-demand value; negative demand is not usable evidence, so water fit is unknown.", "ফসলের পানির চাহিদা ঋণাত্মক দেখানো হয়েছে। এই মান ব্যবহারযোগ্য নয়, তাই পানির উপযোগিতা জানা যায় না।"],
  IRRIGATION_CONFIRMATION_REQUIRED: ["Irrigation confirmation required. The crop profile carries quantified water-demand guidance, but water access was not confirmed, so this prerequisite remains unresolved.", "সেচের ব্যবস্থা নিশ্চিত করা দরকার। ফসলের পানির চাহিদার পরিমাণ সম্পর্কে নির্দেশনা আছে, তবে পানির ব্যবস্থা নিশ্চিত করা হয়নি।"],
  RAINFED_GUIDANCE_REVIEW: ["Rainfed water access does not establish that rainfall will meet this crop's documented water-demand guidance. Rainfall is not assumed to satisfy the requirement.", "চাষ বৃষ্টিনির্ভর হলে শুধু বৃষ্টিতেই ফসলের নথিভুক্ত পানির চাহিদা মিটবে কি না, তা যাচাই করা দরকার।"],
  IRRIGATION_PARTIAL_CONFIRMATION: ["Irrigation is reported as available, but the amount, timing, reliability, and cost are not confirmed. This addresses only part of the prerequisite.", "সেচের ব্যবস্থা আছে বলে জানানো হয়েছে। পানির পরিমাণ, সেচের সময়, নির্ভরযোগ্যতা ও খরচ এখনও নিশ্চিত নয়।"],
};

const codes = {
  ENGINE_TIMEOUT: "CycleAlgo উত্তর দিতে বেশি সময় নিয়েছে। আবার চেষ্টা করুন।",
  ENGINE_UNREACHABLE: "CycleAlgo-এর সঙ্গে সংযোগ করা যায়নি। আবার চেষ্টা করুন।",
  ENGINE_INVALID_RESPONSE: "CycleAlgo থেকে অপ্রত্যাশিত উত্তর এসেছে। ইঞ্জিনের সংস্করণ যাচাই করে আবার চেষ্টা করুন।",
  CLIENT_NETWORK_ERROR: "FosholCycle-এর সঙ্গে সংযোগ করা যায়নি। আবার চেষ্টা করুন।",
  CLIENT_INVALID_RESPONSE: "FosholCycle থেকে অপ্রত্যাশিত উত্তর এসেছে।",
  CLIMATE_EXPOSURE_DEFERRED: "চলতি মৌসুমে আবহাওয়ার প্রভাবের হিসাব পরে যোগ করা হবে (§৬.২)। এই বিকল্পের জন্য চলতি মৌসুমের আবহাওয়ার তথ্য ব্যবহার করা হয়নি।",
  ECONOMICS_UNAVAILABLE: "দাম, খরচ, ফলন বা নগদ প্রবাহের উৎসসহ তথ্য নেই। তাই অর্থনৈতিক হিসাব পাওয়া যায়নি।",
  POWER_OUTLOOK_UNAVAILABLE: "NASA POWER-এর তথ্য দেওয়া হয়নি। তাই চাষের মৌসুমের আবহাওয়ার পরিসর পাওয়া যায়নি।",
  SMAP_CONTEXT_UNAVAILABLE: "SMAP-এর তথ্য পাওয়া যায়নি। তাই মাটির আর্দ্রতা দেখানো হয়নি।",
  DATA_UNAVAILABLE: "ফসলের তথ্য পাওয়া যায়নি। তাই কোনো ফসলক্রম মূল্যায়ন করা যায়নি।",
  UNSUPPORTED_DISTRICT: "এই জেলা পরীক্ষামূলক সেবার আওতায় নেই।",
  CLIMATE_EVIDENCE_MISSING: "তুলনাযোগ্য আবহাওয়ার তথ্য নেই।",
  COMPLETION_EVIDENCE_MISSING: "ফসলক্রম শেষ করার সময় নির্ধারণের তথ্য নেই।",
  DIVERSITY_EVIDENCE_MISSING: "ফসলের পরিবারের বৈচিত্র্য নির্ধারণের তথ্য নেই।",
  METRIC_EVIDENCE_MISSING: "এই পরিমাপের জন্য তথ্য নেই।",
  NO_COMMON_COMPLETE_SEASONS: "তুলনার জন্য সবার সম্পূর্ণ তথ্য আছে এমন মৌসুম নেই।",
  TEMPERATURE_COVERAGE_UNAVAILABLE: "তাপমাত্রার সম্পূর্ণ তথ্য আছে এমন সাধারণ মৌসুম নেই।",
  RAIN_COVERAGE_UNAVAILABLE: "বৃষ্টিপাতের সম্পূর্ণ তথ্য আছে এমন সাধারণ মৌসুম নেই।",
  TEMPERATURE_UNITS_UNAVAILABLE: "তাপমাত্রার একক যাচাই করা যায়নি।",
  RAIN_UNITS_UNAVAILABLE: "বৃষ্টিপাতের একক যাচাই করা যায়নি।",
  UNITS_UNCONFIRMED: "পরিমাপের একক নিশ্চিত নয়।",
  UNITS_INCOMPATIBLE: "পরিমাপের একক সামঞ্জস্যপূর্ণ নয়।",
  district_soil_ph: "জেলার মাটির pH",
  district_soil_texture: "জেলার মাটির বুনট",
  district_soil_drainage: "জেলার মাটির পানি নিষ্কাশন",
  district_soil_salinity: "জেলার মাটির লবণাক্ততা",
  preparation_time: "জমি প্রস্তুতের সময়",
  max_waiting_days_policy: "সর্বোচ্চ অপেক্ষার সময়ের নিয়ম",
  current_season_climate_exposure: "চলতি মৌসুমে আবহাওয়ার প্রভাব",
  crop_water_demand_evidence: "ফসলের পানির চাহিদার তথ্য",
  calendar_evidence: "ফসলের ক্যালেন্ডারের তথ্য",
  duration_reference_stage: "ফসলের জীবনকালের হিসাব শুরুর পর্যায়",
};

const knownMessages = new Map([
  ...Object.values(water),
  ["No candidate or conditional branches available.", "প্রাথমিক যাচাইয়ে উত্তীর্ণ বা শর্তসাপেক্ষ কোনো ফসলক্রম পাওয়া যায়নি।"],
  ["No usable historical evidence for this view.", "এই তুলনার জন্য ব্যবহারযোগ্য অতীতের তথ্য নেই।"],
  ["POWER environment not supplied", codes.POWER_OUTLOOK_UNAVAILABLE],
  ["POWER environment is unavailable.", codes.POWER_OUTLOOK_UNAVAILABLE],
  ["POWER observations are unavailable.", "NASA POWER-এর পর্যবেক্ষণ পাওয়া যায়নি।"],
  ["Completion realizations are unavailable.", "ফসলক্রম শেষ করার উদাহরণসূচি পাওয়া যায়নি।"],
  ["last_complete_data_date not configured", "সম্পূর্ণ তথ্যের শেষ তারিখ নির্ধারণ করা হয়নি।"],
  ["last_complete_data_date is not configured.", "সম্পূর্ণ তথ্যের শেষ তারিখ নির্ধারণ করা হয়নি।"],
  ["crop span unavailable", "ফসলের চাষের সময়সীমা পাওয়া যায়নি।"],
  ["outlook calculation failed", "অতীতের আবহাওয়ার পরিসর হিসাব করা যায়নি।"],
  ["Soil fit is unknown. No local district pH evidence was supplied; pH fit is unknown rather than an automatic pass.", "জেলার মাটির pH-এর স্থানীয় তথ্য দেওয়া হয়নি। তাই মাটি উপযুক্ত কি না, তা জানা যায় না।"],
  ["No preparation-time evidence was supplied for this crop; harvest is known but field readiness is unknown, never zero.", "এই ফসলের জন্য জমি প্রস্তুতের সময়ের তথ্য নেই। ফসল তোলার সময় জানা আছে, তবে জমি কখন প্রস্তুত হবে জানা নেই। প্রস্তুতির সময় শূন্য ধরা হয়নি।"],
  ["The variety duration range does not record whether it starts at sowing or transplanting; timing is conditional until that reference stage is verified.", "জাতটির জীবনকালের হিসাব বীজ বোনা থেকে নাকি চারা রোপণ থেকে শুরু, তা নথিভুক্ত নেই। শুরুর পর্যায় যাচাই না হওয়া পর্যন্ত সময়ের হিসাব শর্তসাপেক্ষ।"],
  ["This crop is transplanted. Seedling/nursery age is recorded but not added to variety duration because the duration reference stage is not confirmed by the crop data.", "এই ফসল চারা রোপণ করে চাষ করা হয়। চারার বয়স নথিভুক্ত আছে। জাতটির জীবনকাল কোন পর্যায় থেকে গণনা করা হয়েছে তা নিশ্চিত না হওয়ায় চারার বয়স সেই সময়ের সঙ্গে যোগ করা হয়নি।"],
  ["Preparation time is unknown, so the crop window range is shown only as the next planting opportunity. This does not claim that the crop completes in time.", "জমি প্রস্তুতের সময় জানা নেই। দেখানো সময়সীমা পরের ফসল রোপণের সম্ভাব্য সুযোগ বোঝায়। সময়মতো ফসল তোলা যাবে কি না, তা নিশ্চিত নয়।"],
  ["No maximum waiting policy is configured; long waits are shown but are not cut off.", "সর্বোচ্চ অপেক্ষার নিয়ম নির্ধারিত নেই। দীর্ঘ অপেক্ষার বিকল্পগুলোও দেখানো হয়েছে।"],
  ["Candidate group is empty; no candidate branches were ranked.", "প্রাথমিক যাচাইয়ে উত্তীর্ণ কোনো ফসলক্রম না থাকায় এই দলের অবস্থান নির্ধারণ করা হয়নি।"],
  ["Conditional group is empty; no conditional branches were ranked.", "শর্তসাপেক্ষ কোনো ফসলক্রম না থাকায় এই দলের অবস্থান নির্ধারণ করা হয়নি।"],
  ["No branch has a comparable metric; no winner is forced.", "কোনো ফসলক্রমের তুলনাযোগ্য মান নেই। সেরা ফসলক্রম নির্ধারণ করা হয়নি।"],
  ["Candidate group has no branch with a comparable metric.", "প্রাথমিক যাচাইয়ে উত্তীর্ণ দলের কোনো ফসলক্রমের তুলনাযোগ্য মান নেই।"],
  ["Conditional group has no branch with a comparable metric.", "শর্তসাপেক্ষ দলের কোনো ফসলক্রমের তুলনাযোগ্য মান নেই।"],
  ["Family-count ordering is a product convention, not a soil-health ranking; legume presence is reported separately.", "এই তুলনায় উদ্ভিদ পরিবারের সংখ্যা ধরে ফসলক্রম সাজানো হয়। এটি মাটির স্বাস্থ্যের ক্রম নয়। ডালজাতীয় ফসলের উপস্থিতি আলাদাভাবে দেখানো হয়।"],
  ["Climate views use only common complete historical seasons; missing evidence and branches without a common season set are unranked.", "আবহাওয়ার তুলনায় কেবল সবার জন্য সম্পূর্ণ তথ্য আছে এমন অতীতের মৌসুম ব্যবহার করা হয়েছে। প্রয়োজনীয় তথ্য বা অভিন্ন মৌসুম না থাকলে ফসলক্রমের অবস্থান নির্ধারণ করা হয় না।"],
  ["Three crop summaries are equally weighted as a disclosed product convention; this is not duration neutrality or agricultural suitability.", "এই তুলনার নিয়মে তিনটি ফসলের সারাংশ সমান ওজনে ধরা হয়েছে। এতে চাষের সময়ের পার্থক্য দূর হয় না এবং কৃষিগত উপযোগিতা নির্ধারিত হয় না।"],
  ["Date outside planning range", "তারিখটি পরিকল্পনার অনুমোদিত সীমার বাইরে।"],
  ["FosholCycle returned an unexpected response.", codes.CLIENT_INVALID_RESPONSE],
  ["The planner could not reach FosholCycle. Try again.", codes.CLIENT_NETWORK_ERROR],
]);

const prefixes = {
  calendar: "ফসলের ক্যালেন্ডার",
  soil: "মাটি",
  water: "পানি",
  rotation: "ফসলক্রম",
  "next planting": "পরের রোপণ",
};

export function translateEngineMessage(message, code, locale) {
  if (locale.language === "en") return null;
  if (Object.hasOwn(water, code)) return water[code][1];
  if (Object.hasOwn(codes, code)) return codes[code];
  if (!message) return null;
  if (Object.hasOwn(codes, message)) return codes[message];
  if (knownMessages.has(message)) return knownMessages.get(message);

  const { number } = locale;
  const prefix = message.match(/^([a-zA-Z ]+): (.+)$/);
  if (prefix && Object.hasOwn(prefixes, prefix[1].toLowerCase())) {
    const translated = translateEngineMessage(prefix[2], undefined, locale);
    if (translated) return `${prefixes[prefix[1].toLowerCase()]}: ${translated}`;
  }
  const climate = message.match(/^(TEMPERATURE|RAIN)_(UNITS|COVERAGE)_UNAVAILABLE: /);
  if (climate) {
    const units = message.match(/\bUNITS_(UNCONFIRMED|INCOMPATIBLE)\b/);
    const label = codes[`${climate[1]}_${climate[2]}_UNAVAILABLE`];
    return units ? `${label} ${codes[units[0]]}` : label;
  }
  const provenance = message.match(/^TEMPERATURE_PROVENANCE_UNVERIFIED: no EcoCrop entry for (.+)\.$/);
  if (provenance) {
    return `তাপমাত্রার নির্দেশনার উৎস যাচাই করা যায়নি। এই ফসলগুলোর জন্য EcoCrop-এ তথ্য নেই: ${provenance[1]}।`;
  }

  const noCandidates = message.match(/^No candidate branches - (\d+) conditional branches? (shown\.|available; select a first crop to view them\.)$/);
  if (noCandidates) {
    const detail = noCandidates[2] === "shown." ? "দেখানো হয়েছে।" : "আছে। দেখতে প্রথম ফসল বেছে নিন।";
    return `প্রাথমিক যাচাইয়ে উত্তীর্ণ কোনো ফসলক্রম নেই। ${number(Number(noCandidates[1]))}টি শর্তসাপেক্ষ ফসলক্রম ${detail}`;
  }
  const summary = message.match(/^(\d+) candidate branches and (\d+) conditional branches? (shown\.|available; select a first crop to view them\.)$/);
  if (summary) {
    const detail = summary[3] === "shown." ? "দেখানো হয়েছে।" : "আছে। দেখতে প্রথম ফসল বেছে নিন।";
    return `প্রাথমিক যাচাইয়ে উত্তীর্ণ ${number(Number(summary[1]))}টি এবং শর্তসাপেক্ষ ${number(Number(summary[2]))}টি ফসলক্রম ${detail}`;
  }
  const wait = message.match(/^The next documented preferred window starts (\d{4}-\d{2}-\d{2}) \((\d+) days? after the proposed date\), within the configured maximum waiting limit of (\d+) days\. This is a future option, not a plant-now option\.$/);
  if (wait) {
    return `নথিভুক্ত পরবর্তী উপযুক্ত রোপণের সময় শুরু ${formatDate(wait[1], locale)}। এটি প্রস্তাবিত তারিখের ${number(Number(wait[2]))} দিন পরে এবং সর্বোচ্চ ${number(Number(wait[3]))} দিনের অপেক্ষার সীমার মধ্যে। রোপণের এই সুযোগটি ভবিষ্যতের জন্য।`;
  }
  const late = message.match(/^The proposed date is after the preferred window but inside the documented supported-late window \(to (\d{4}-\d{2}-\d{2})\)\. The preferred end is not a proven biological deadline; late planting carries documented risk\.$/);
  if (late) {
    return `প্রস্তাবিত তারিখ উপযুক্ত সময়সীমার পরে, তবে দেরিতে রোপণের নথিভুক্ত সীমার মধ্যে (${formatDate(late[1], locale)} পর্যন্ত)। উপযুক্ত সময়ের শেষ দিনটি নিশ্চিত জৈবিক সীমা নয়। দেরিতে রোপণের ঝুঁকি নথিভুক্ত আছে।`;
  }
  const approx = message.match(/^The proposed date is inside the documented preferred window \((\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})\), but the boundary is approximate \(([^)]+)\), not exact\. The window end is not a proven biological deadline\.$/);
  if (approx) {
    return `প্রস্তাবিত তারিখ নথিভুক্ত উপযুক্ত সময়সীমার মধ্যে (${formatDate(approx[1], locale)} থেকে ${formatDate(approx[2], locale)})। সময়সীমাটি আনুমানিক (${approx[3]})। শেষ দিনটি নিশ্চিত জৈবিক সীমা নয়।`;
  }
  const transferred = message.match(/^The window is not Rajshahi-exact \(([^)]+)\); it cannot support a calendar pass for this district even when the date falls inside the encoded dates\.$/);
  if (transferred) {
    return `রোপণের সময়সীমা রাজশাহীর জন্য সুনির্দিষ্ট নয় (${transferred[1]})। তারিখ ওই সীমার মধ্যে হলেও এই জেলার ক্যালেন্ডার যাচাইয়ে উত্তীর্ণ ধরা যায় না।`;
  }
  const adjacent = message.match(/^Both the previous crop and this crop are in ([\w-]+)\. Same-family repetition is a diversity caution only; it is not rejected because no structured, sourced restriction exists\.$/);
  if (adjacent) {
    return `আগের ফসল ও এই ফসল দুটিই ${adjacent[1]} পরিবারের। একই পরিবার পুনরাবৃত্তি হওয়া বৈচিত্র্যসংক্রান্ত সতর্কতা। উৎসসহ কোনো নির্দিষ্ট নিষেধাজ্ঞা না থাকায় ফসলক্রমটি বাদ দেওয়া হয়নি।`;
  }
  const repeated = message.match(/^The current crop family ([\w-]+) also appears at position\(s\) ([\d, ]+) earlier in the three-crop path\. Repeated families are a diversity caution only; they are not rejected because no structured, sourced restriction exists\.$/);
  if (repeated) {
    const positions = repeated[2].split(",").map((value) => number(Number(value.trim()))).join(", ");
    return `তিন ফসলের এই ক্রমে ${repeated[1]} পরিবার আগেও ছিল (অবস্থান ${positions})। পুনরাবৃত্তি বৈচিত্র্যসংক্রান্ত সতর্কতা। উৎসসহ নির্দিষ্ট নিষেধাজ্ঞা না থাকায় ফসলক্রমটি বাদ দেওয়া হয়নি।`;
  }
  const overlap = message.match(/^Top two completion ranges overlap in the (candidate|conditional) group \(([^)]+)\); the order is not a definitive timing winner\.$/);
  if (overlap) {
    const group = locale.t(overlap[1] === "candidate" ? "Candidate" : "Conditional");
    return `${group} দলের প্রথম দুটি ফসলক্রমের শেষ করার সময়সীমা আংশিক মিলে যায় (${overlap[2]})। কোনটি নিশ্চিতভাবে আগে শেষ হবে, তা এই ক্রম থেকে বোঝা যায় না।`;
  }
  const tie = message.match(/^(Candidate|Conditional) group: (\d+) branches share the top value (-?\d+(?:\.\d+)?(?:e[+-]?\d+)?); branch_id order is display-only\.$/i);
  if (tie) {
    const group = locale.t(tie[1].toLowerCase() === "candidate" ? "Candidate" : "Conditional");
    return `${group} দলের ${number(Number(tie[2]))}টি ফসলক্রম একই শীর্ষ মান পেয়েছে (${number(Number(tie[3]), 20)})। শাখার আইডি শুধু দেখানোর ক্রম ঠিক করে।`;
  }
  return null;
}
