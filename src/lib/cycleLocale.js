import { bangla } from "./cycleCopy.js";

export function readCycleLanguage(value) {
  return value === "en" ? "en" : "bn";
}

const cropNames = {
  aman_br11: "আমন ধান",
  boro_brri_dhan28: "বোরো ধান",
  wheat_bari_gom33: "গম",
  mustard_binasarisha9: "সরিষা",
  lentil_binamasur9: "মসুর",
  mung_bari_mung6_kharif1: "মুগ",
  maize_rabi_bari_hybrid13: "ভুট্টা",
  potato_bari_alu41: "আলু",
};

function createCycleLocale(language) {
  const bn = language === "bn";
  const locale = bn ? "bn-BD" : "en-GB";
  const dateFormatter = new Intl.DateTimeFormat(locale, {
    day: "numeric", month: bn ? "long" : "short", year: "numeric", calendar: "gregory", timeZone: "UTC",
  });
  const numbers = new Map();

  function number(value, maximumFractionDigits = 0, useGrouping = false) {
    const key = `${maximumFractionDigits}:${useGrouping}`;
    if (!numbers.has(key)) {
      numbers.set(key, new Intl.NumberFormat(locale, { maximumFractionDigits, useGrouping }));
    }
    return numbers.get(key).format(value);
  }

  function t(message, values = {}) {
    const template = bn && Object.hasOwn(bangla, message) ? bangla[message] : message;
    return template.replace(/\{(\w+)\}/g, (token, key) => {
      if (!Object.hasOwn(values, key)) return token;
      const value = values[key];
      return typeof value === "number" ? number(value, 20) : value;
    });
  }

  function cropName(crop) {
    const original = crop.name_en || crop.crop_id;
    if (bn) {
      const supplied = typeof crop.name_bn === "string" ? crop.name_bn.trim() : "";
      const translated = supplied || (Object.hasOwn(cropNames, crop.crop_id) ? cropNames[crop.crop_id] : null);
      if (translated) return { text: translated, lang: "bn" };
    }
    return { text: original, lang: "en" };
  }

  return { language, t, number, dateFormatter, cropName };
}

export const cycleLocales = {
  bn: createCycleLocale("bn"),
  en: createCycleLocale("en"),
};
