import { translateEngineMessage } from "@/lib/cycleEngineCopy";
import { useCycleLanguage } from "./CycleLanguage";

export function CropName({ crop }) {
  const { cropName } = useCycleLanguage();
  const { text, lang } = cropName(crop);
  return <span lang={lang}>{text}</span>;
}

export function RotationName({ branch }) {
  return branch.crops.map((crop, index) => (
    <span key={index}>{index > 0 && " → "}<CropName crop={crop} /></span>
  ));
}

export function EngineMessage({ message, code, humanize = false }) {
  const locale = useCycleLanguage();
  const translated = translateEngineMessage(message, code, locale);
  if (translated) return translated;
  if (!message) return null;
  if (locale.language === "bn") {
    if (/\p{Script=Bengali}/u.test(message)) return message;
    return <>{locale.t("Original from CycleAlgo (English)")}: <span lang="en">{message}</span></>;
  }
  return humanize ? message.replaceAll("_", " ").replace(/\bph\b/g, "pH") : message;
}
