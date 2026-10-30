import {
  advisoryScenarios,
  modelAdvisoryById,
  modelAdvisoryIndex,
  type AdvisoryScenario,
  type ModelAdvisory,
} from "./model-advisory-index";
import { stemSearchText } from "./stem-labels";
import type { CatalogModel, CatalogQuery } from "./types";

export const AUDIO_BUSINESS_REQUIREMENT = "分轨输出按 stem 返回 48000Hz PCM_24 WAV，支持预览和单轨下载";

export const scenarioOptions = advisoryScenarios.map((scenario) => ({
  value: scenario.id,
  label: scenario.label,
}));

export const sortOptions = [
  { value: "recommended", label: "推荐优先" },
  { value: "local", label: "已下载优先" },
  { value: "size_asc", label: "体积从小到大" },
  { value: "size_desc", label: "体积从大到小" },
  { value: "name", label: "名称排序" },
];

export function getScenario(id: string): AdvisoryScenario {
  return advisoryScenarios.find((scenario) => scenario.id === id) ?? advisoryScenarios[0];
}

export function getAdvisory(modelId: string): ModelAdvisory | null {
  return modelAdvisoryById[modelId] ?? null;
}

export function recommendationLabel(advisory: ModelAdvisory | null | undefined): string {
  if (advisory?.recommendationLevel === "primary") return "首选";
  if (advisory?.recommendationLevel === "featured") return "精选";
  return "";
}

function recommendationRank(advisory: ModelAdvisory | null | undefined): number {
  if (advisory?.recommendationLevel === "primary") return 2;
  if (advisory?.recommendationLevel === "featured") return 1;
  return 0;
}

export function uniqueOptions(values: string[]): Array<{ value: string; label: string }> {
  return [
    { value: "", label: "全部" },
    ...Array.from(new Set(values.filter(Boolean)))
      .sort((a, b) => a.localeCompare(b, "zh-Hans-CN"))
      .map((value) => ({ value, label: value })),
  ];
}

export const primaryCategoryOptions = uniqueOptions(modelAdvisoryIndex.map((entry) => entry.primaryCategoryCn));
export const secondaryCategoryOptions = uniqueOptions(modelAdvisoryIndex.map((entry) => entry.secondaryCategoryCn));
export const architectureOptions = uniqueOptions(modelAdvisoryIndex.map((entry) => entry.architecture));
export const modelTypeOptions = uniqueOptions(modelAdvisoryIndex.map((entry) => entry.modelType));
export const confidenceOptions = [
  { value: "", label: "全部" },
  { value: "high", label: "高" },
  { value: "medium", label: "中" },
  { value: "low", label: "低" },
];
export const sizeTierOptions = [
  { value: "", label: "全部" },
  { value: "小", label: "小" },
  { value: "中", label: "中" },
  { value: "大", label: "大" },
  { value: "超大", label: "超大" },
];

export function filterAndSortModels(models: CatalogModel[], query: CatalogQuery): CatalogModel[] {
  const q = query.q.trim().toLowerCase();
  const filtered = models.filter((model) => {
    const advisory = getAdvisory(model.id);
    if (!advisory) {
      return false;
    }
    if (query.recommendedOnly && advisory.recommendationLevel === "none") {
      return false;
    }
    if (query.selectionMode === "scenario") {
      if (!advisory.scenarios.includes(query.scenario as never)) {
        return false;
      }
      if (advisory.classificationConfidence === "low" && advisory.recommendationLevel === "none") {
        return false;
      }
    } else {
      if (query.primaryCategoryCn && advisory.primaryCategoryCn !== query.primaryCategoryCn) return false;
      if (query.secondaryCategoryCn && advisory.secondaryCategoryCn !== query.secondaryCategoryCn) return false;
      if (query.architecture && advisory.architecture !== query.architecture) return false;
      if (query.modelType && advisory.modelType !== query.modelType) return false;
      if (query.confidence && advisory.classificationConfidence !== query.confidence) return false;
      if (query.sizeTier && advisory.sizeTier !== query.sizeTier) return false;
      if (query.targetStem.trim()) {
        const targetQuery = query.targetStem.trim().toLowerCase();
        const targetText = [
          advisory.targetStem,
          advisory.configInstruments,
          advisory.configTargetInstrument,
          stemSearchText(advisory.targetStem),
          stemSearchText(advisory.configInstruments),
          stemSearchText(advisory.configTargetInstrument),
        ].join(" ").toLowerCase();
        if (!targetText.includes(targetQuery)) return false;
      }
    }
    if (q && !advisory.searchText.includes(q) && !model.id.toLowerCase().includes(q)) {
      return false;
    }
    return true;
  });

  return filtered.sort((a, b) => compareModels(a, b, query));
}

function scenarioRank(advisory: ModelAdvisory | null | undefined, scenario: string): number {
  return advisory?.scenarioRanks?.[scenario as never] ?? Number.POSITIVE_INFINITY;
}

function compareModels(a: CatalogModel, b: CatalogModel, query: CatalogQuery): number {
  const sort = query.sort;
  const aInfo = getAdvisory(a.id);
  const bInfo = getAdvisory(b.id);
  if (sort === "local") {
    const localDelta = Number(b.pymss.local.complete) - Number(a.pymss.local.complete);
    if (localDelta) return localDelta;
  }
  if (sort === "size_asc") return a.pymss.size_bytes - b.pymss.size_bytes;
  if (sort === "size_desc") return b.pymss.size_bytes - a.pymss.size_bytes;
  if (sort === "name") return a.id.localeCompare(b.id);

  if (query.selectionMode === "scenario") {
    const aScenarioRank = scenarioRank(aInfo, query.scenario);
    const bScenarioRank = scenarioRank(bInfo, query.scenario);
    if (aScenarioRank !== bScenarioRank) return aScenarioRank - bScenarioRank;
  }
  const recommendationDelta = recommendationRank(bInfo) - recommendationRank(aInfo);
  if (recommendationDelta) return recommendationDelta;
  const localDelta = Number(b.pymss.local.complete) - Number(a.pymss.local.complete);
  if (localDelta) return localDelta;
  const priorityDelta = (bInfo?.priority ?? 0) - (aInfo?.priority ?? 0);
  if (priorityDelta) return priorityDelta;
  const sizeDelta = a.pymss.size_bytes - b.pymss.size_bytes;
  if (sizeDelta) return sizeDelta;
  return a.id.localeCompare(b.id);
}
