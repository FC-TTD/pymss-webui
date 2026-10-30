import { modelAdvisoryById, type ModelAdvisory } from "./model-advisory-index";

export interface ModelNote {
  ability: string;
  usage: string;
  sourceRepresentative: string;
}

export function getModelAdvisory(modelId: string): ModelAdvisory | null {
  return modelAdvisoryById[modelId] ?? null;
}

export function getModelNote(modelId: string): ModelNote | null {
  return getModelAdvisory(modelId)?.note ?? null;
}

export function isRecommendedModel(modelId: string): boolean {
  const advisory = getModelAdvisory(modelId);
  return Boolean(advisory && advisory.recommendationLevel !== "none");
}
