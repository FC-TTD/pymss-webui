const STEM_LABELS: Record<string, string> = {
  vocals: "人声",
  vocal: "人声",
  voice: "人声",
  voices: "人声",
  lead: "主唱",
  lead_vocals: "主唱",
  lead_vocal: "主唱",
  back: "伴唱",
  back_vocal: "和声",
  backing_vocals: "和声",
  backing_vocal: "和声",
  backvocals: "和声",
  chorus: "合唱",
  choir: "合唱",
  male: "男声",
  female: "女声",
  singer_1: "歌手1",
  singer_2: "歌手2",
  soprano: "女高音",
  alto: "女低音",
  tenor: "男高音",
  speech: "语音",
  dialogue: "对白",
  dialog: "对白",
  breath: "呼吸声",
  aspiration: "气声",
  instrumental: "伴奏",
  inst: "伴奏",
  instrument: "伴奏",
  instruments: "伴奏",
  music: "音乐",
  accompaniment: "伴奏",
  accomp: "伴奏",
  non_vocals: "非人声",
  no_vocals: "无人声伴奏",
  other: "其他乐器",
  others: "其他乐器",
  "6_stems": "六分轨",
  rest: "其余声部",
  effects: "音效",
  difference: "差分信号",
  similarity: "相似声部",
  drums: "鼓组",
  drum: "鼓",
  drum_bass: "鼓和贝斯",
  no_drum_bass: "非鼓贝斯",
  drums_percussion: "鼓组/打击乐",
  kick: "底鼓",
  bass_drum: "底鼓",
  snare: "军鼓",
  hh: "踩镲",
  hihat: "踩镲",
  hi_hat: "踩镲",
  crash: "吊镲",
  ride: "叮叮镲",
  cymbals: "镲片",
  cymbal: "镲片",
  toms: "桶鼓",
  tom: "桶鼓",
  percussion: "打击乐",
  bass: "贝斯",
  double_bass: "低音提琴",
  guitar: "吉他",
  guitars: "吉他",
  electric_guitar: "电吉他",
  acoustic_guitar: "木吉他",
  dobro: "多布罗吉他",
  banjo: "班卓琴",
  mandolin: "曼陀林",
  ukulele: "尤克里里",
  sitar: "西塔琴",
  piano: "钢琴",
  digital_piano: "电钢琴",
  harpsichord: "羽管键琴",
  keys: "键盘",
  keyboard: "键盘",
  keyboards: "键盘",
  synth: "合成器",
  synthesizer: "合成器",
  strings: "弦乐",
  string: "弦乐",
  bowed_strings: "拉弦乐",
  violin: "小提琴",
  viola: "中提琴",
  cello: "大提琴",
  brass: "铜管",
  french_horn: "圆号",
  trumpet: "小号",
  trombone: "长号",
  tuba: "大号",
  wind: "管乐",
  woodwind: "木管",
  woodwinds: "木管",
  flute: "长笛",
  clarinet: "单簧管",
  oboe: "双簧管",
  bassoon: "巴松",
  sax: "萨克斯",
  saxophone: "萨克斯",
  harmonica: "口琴",
  organ: "风琴",
  accordion: "手风琴",
  harp: "竖琴",
  bells: "钟琴",
  glockenspiel: "钟琴",
  marimba: "马林巴",
  timpani: "定音鼓",
  congas: "康加鼓",
  tambourine: "铃鼓",
  triangle: "三角铁",
  wind_chimes: "风铃",
  mallet: "槌击乐器",
  reed: "簧管",
  dry: "干声",
  no_dry: "非干声",
  wet: "湿声",
  reverb: "混响",
  noreverb: "无混响",
  no_reverb: "无混响",
  dereverb: "去混响",
  echo: "回声",
  no_echo: "去回声",
  noise: "噪声",
  no_noise: "无噪声",
  denoise: "降噪",
  bleed: "串音",
  debleed: "去串音",
  bleedless: "低串音",
  crowd: "环境人群声",
  ambience: "环境声",
  ambient: "环境声",
  restored: "修复后音轨",
  restored_vocal: "修复后人声",
  addition: "补充残差信号",
  center: "中置声道",
  mono: "单声道",
  stereo: "立体声",
  wide: "宽声场",
  side: "侧声道",
  l: "左声道",
  r: "右声道",
  left: "左声道",
  right: "右声道",
};

const TARGET_SPLIT_PATTERN = /([/|,，、+&]+)/;

export function stemChineseLabel(stem: string): string {
  const normalized = stem.trim().toLowerCase().replace(/[\s-]+/g, "_");
  if (!normalized) return "";
  if (STEM_LABELS[normalized]) return STEM_LABELS[normalized];
  if (normalized.includes("vocal") || normalized.includes("vox")) return "人声";
  if (normalized.includes("inst") || normalized.includes("accomp")) return "伴奏";
  if (normalized.includes("drum")) return "鼓组";
  if (normalized.includes("bass")) return "贝斯";
  if (normalized.includes("guitar")) return "吉他";
  if (normalized.includes("piano")) return "钢琴";
  if (normalized.includes("breath") || normalized.includes("aspiration")) return "呼吸声";
  if (normalized.includes("noise")) return "噪声";
  if (normalized.includes("echo")) return "回声";
  if (normalized.includes("reverb")) return "混响";
  if (normalized.includes("bleed")) return "串音";
  if (normalized.includes("speech") || normalized.includes("dialog")) return "对白/语音";
  if (normalized.includes("restore")) return "修复后音轨";
  return "目标音轨";
}

export function formatStem(stem: string): string {
  const text = stem.trim();
  if (!text) return "-";
  return `${text}（${stemChineseLabel(text)}）`;
}

export function formatStemTargets(targets: string | null | undefined): string {
  const text = targets?.trim();
  if (!text) return "-";
  return text
    .split(TARGET_SPLIT_PATTERN)
    .map((part) => {
      if (!part.trim()) return part;
      if (TARGET_SPLIT_PATTERN.test(part)) return part;
      return formatStem(part);
    })
    .join("");
}

export function stemSearchText(targets: string | null | undefined): string {
  const text = targets?.trim();
  if (!text) return "";
  return text
    .split(TARGET_SPLIT_PATTERN)
    .filter((part) => part.trim() && !TARGET_SPLIT_PATTERN.test(part))
    .map((part) => stemChineseLabel(part))
    .join(" ");
}
