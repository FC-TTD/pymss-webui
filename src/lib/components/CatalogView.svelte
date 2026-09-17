<script lang="ts">
  import { Download, Info, Loader2, SlidersHorizontal, Sparkles } from "@lucide/svelte";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Card, CardContent, CardHeader, CardTitle } from "$lib/components/ui/card/index.js";
  import { Checkbox } from "$lib/components/ui/checkbox/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import { Label } from "$lib/components/ui/label/index.js";
  import * as Table from "$lib/components/ui/table/index.js";
  import SelectField from "./SelectField.svelte";
  import { formatBytes } from "../params";
  import {
    AUDIO_BUSINESS_REQUIREMENT,
    architectureOptions,
    confidenceOptions,
    filterAndSortModels,
    getAdvisory,
    getScenario,
    modelTypeOptions,
    primaryCategoryOptions,
    recommendationLabel,
    scenarioOptions,
    secondaryCategoryOptions,
    sizeTierOptions,
    sortOptions,
  } from "../model-selection";
  import { formatStemTargets } from "../stem-labels";
  import type { CatalogListResponse, CatalogModel, CatalogQuery } from "../types";

  export let catalog: CatalogListResponse | null;
  export let selectedCatalog: CatalogModel | null;
  export let selectedDownloadModels: string[];
  export let catalogQuery: CatalogQuery;
  export let busyAction: string | null;
  export let onApplyFilters: () => void;
  export let onShowDetail: (model: string) => void;
  export let onDownload: (model: string) => void;
  export let onDownloadSelected: () => void;
  export let onToggleDownloadSelection: (model: string, checked: boolean) => void;
  export let onSetDownloadSelection: (models: string[]) => void;
  export let onSetLoadTarget: (model: string) => void;
  export let onCloseDetail: () => void;

  const supportedOptions = [
    { value: "true", label: "仅支持" },
    { value: "all", label: "全部" },
    { value: "false", label: "不支持" },
  ];

  const localOptions = [
    { value: "all", label: "全部" },
    { value: "complete", label: "已下载" },
    { value: "missing", label: "未下载" },
  ];

  $: activeScenario = getScenario(catalogQuery.scenario);
  $: filteredModels = filterAndSortModels(catalog?.data ?? [], catalogQuery);
  $: selectedVisibleCount = filteredModels.filter((model) => selectedDownloadModels.includes(model.id)).length;
  $: visibleModels = filteredModels.map((model) => model.id);
  $: allVisibleSelected = visibleModels.length > 0 && visibleModels.every((model) => selectedDownloadModels.includes(model));

  function setVisibleSelection(checked: boolean): void {
    if (checked) {
      onSetDownloadSelection([...selectedDownloadModels, ...visibleModels]);
    } else {
      onSetDownloadSelection(selectedDownloadModels.filter((model) => !visibleModels.includes(model)));
    }
  }

  function setMode(mode: CatalogQuery["selectionMode"]): void {
    catalogQuery.selectionMode = mode;
    catalogQuery.sort = "recommended";
  }
</script>

<section class="space-y-6">
  <div class="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
    <div>
      <h1 class="text-[30px] font-medium leading-tight tracking-normal">模型目录</h1>
      <p class="mt-2 text-sm text-muted-foreground">
        {AUDIO_BUSINESS_REQUIREMENT}，共 {catalog?.pymss.total ?? 0} 个模型，当前显示 {filteredModels.length} 个
      </p>
    </div>
    <div class="flex flex-wrap gap-2">
      <Button variant="outline" type="button" onclick={onDownloadSelected} disabled={busyAction !== null || !selectedDownloadModels.length}>
        {#if busyAction === "download"}
          <Loader2 class="size-4 animate-spin" />
        {:else}
          <Download class="size-4" />
        {/if}
        下载所选（{selectedDownloadModels.length}）
      </Button>
      <Button form="catalog-search-form" type="submit" disabled={busyAction !== null}>
        {#if busyAction === "catalog"}
          <Loader2 class="size-4 animate-spin" />
        {/if}
        刷新
      </Button>
    </div>
  </div>

  <div class="flex flex-wrap gap-2">
    <Button
      type="button"
      variant={catalogQuery.selectionMode === "scenario" ? "default" : "outline"}
      onclick={() => setMode("scenario")}
    >
      <Sparkles class="size-4" />
      场景选型
    </Button>
    <Button
      type="button"
      variant={catalogQuery.selectionMode === "advanced" ? "default" : "outline"}
      onclick={() => setMode("advanced")}
    >
      <SlidersHorizontal class="size-4" />
      高级筛选
    </Button>
  </div>

  <Card>
    <CardContent>
      <form id="catalog-search-form" class="space-y-4" on:submit|preventDefault={onApplyFilters}>
        {#if catalogQuery.selectionMode === "scenario"}
          <div class="grid gap-3 lg:grid-cols-[minmax(0,1.2fr)_10rem_10rem_10rem]">
            <SelectField
              id="catalog-scenario"
              label="业务场景"
              value={catalogQuery.scenario}
              options={scenarioOptions}
              onValueChange={(value) => (catalogQuery.scenario = value)}
            />
            <SelectField
              id="catalog-local"
              label="本地状态"
              value={catalogQuery.local}
              options={localOptions}
              onValueChange={(value) => (catalogQuery.local = value as CatalogQuery["local"])}
            />
            <SelectField
              id="catalog-supported"
              label="支持状态"
              value={catalogQuery.supported}
              options={supportedOptions}
              onValueChange={(value) => (catalogQuery.supported = value as CatalogQuery["supported"])}
            />
            <SelectField
              id="catalog-sort"
              label="排序"
              value={catalogQuery.sort}
              options={sortOptions}
              onValueChange={(value) => (catalogQuery.sort = value as CatalogQuery["sort"])}
            />
          </div>
          <div class="rounded-sm border border-border bg-muted/35 p-3 text-sm leading-6">
            <div class="font-medium">{activeScenario.label}</div>
            <div class="text-muted-foreground">{activeScenario.description}</div>
            <div class="text-muted-foreground">典型输出：{activeScenario.outputHint}</div>
          </div>
        {:else}
          <div class="grid gap-3 xl:grid-cols-4">
            <SelectField id="catalog-primary-cn" label="一级分类" value={catalogQuery.primaryCategoryCn} options={primaryCategoryOptions} onValueChange={(value) => (catalogQuery.primaryCategoryCn = value)} />
            <SelectField id="catalog-secondary-cn" label="二级分类" value={catalogQuery.secondaryCategoryCn} options={secondaryCategoryOptions} onValueChange={(value) => (catalogQuery.secondaryCategoryCn = value)} />
            <SelectField id="catalog-architecture" label="架构" value={catalogQuery.architecture} options={architectureOptions} onValueChange={(value) => (catalogQuery.architecture = value)} />
            <SelectField id="catalog-model-type" label="模型类型" value={catalogQuery.modelType} options={modelTypeOptions} onValueChange={(value) => (catalogQuery.modelType = value)} />
            <SelectField id="catalog-confidence" label="分类置信度" value={catalogQuery.confidence} options={confidenceOptions} onValueChange={(value) => (catalogQuery.confidence = value)} />
            <SelectField id="catalog-size-tier" label="体积" value={catalogQuery.sizeTier} options={sizeTierOptions} onValueChange={(value) => (catalogQuery.sizeTier = value)} />
            <SelectField id="catalog-local-advanced" label="本地状态" value={catalogQuery.local} options={localOptions} onValueChange={(value) => (catalogQuery.local = value as CatalogQuery["local"])} />
            <SelectField id="catalog-sort-advanced" label="排序" value={catalogQuery.sort} options={sortOptions} onValueChange={(value) => (catalogQuery.sort = value as CatalogQuery["sort"])} />
          </div>
          <div class="grid gap-3 md:grid-cols-2">
            <div class="grid gap-1.5">
              <Label for="catalog-target-stem">输出目标 / instruments</Label>
              <Input id="catalog-target-stem" class="h-9 text-sm" bind:value={catalogQuery.targetStem} placeholder="vocals / dry / piano / center" />
            </div>
            <SelectField
              id="catalog-supported-advanced"
              label="支持状态"
              value={catalogQuery.supported}
              options={supportedOptions}
              onValueChange={(value) => (catalogQuery.supported = value as CatalogQuery["supported"])}
            />
          </div>
        {/if}

        <div class="grid gap-3 md:grid-cols-[minmax(0,1fr)_auto_auto] md:items-end">
          <div class="grid gap-1.5">
            <Label for="catalog-search">关键词</Label>
            <Input id="catalog-search" class="h-9 text-sm" bind:value={catalogQuery.q} placeholder="模型名、中文分类、备注、stem、架构" />
          </div>
          <label class="flex h-9 items-center gap-2 text-sm">
            <Checkbox bind:checked={catalogQuery.recommendedOnly} />
            <span>仅看推荐</span>
          </label>
          <label class="flex h-9 items-center gap-2 text-sm">
            <Checkbox checked={allVisibleSelected} onCheckedChange={(checked) => setVisibleSelection(checked === true)} />
            <span>全选当前结果（{filteredModels.length}）</span>
          </label>
        </div>
      </form>
    </CardContent>
  </Card>

  <Card class="py-0">
    <CardContent class="px-0">
      <Table.Root>
        <Table.Body>
          {#each filteredModels as model}
            {@const advisory = getAdvisory(model.id)}
            {@const modelRecommendationLabel = recommendationLabel(advisory)}
            <Table.Row>
              <Table.Cell class="w-10 p-3 align-top">
                <Checkbox checked={selectedDownloadModels.includes(model.id)} onCheckedChange={(checked) => onToggleDownloadSelection(model.id, checked === true)} aria-label={`选择 ${model.id}`} />
              </Table.Cell>
              <Table.Cell class="whitespace-normal p-3">
                <div class="max-w-3xl">
                  <div class="flex flex-wrap items-center gap-2">
                    <span class="break-all font-medium">{model.id}</span>
                    {#if modelRecommendationLabel}<Badge>{modelRecommendationLabel}</Badge>{/if}
                    {#if model.pymss.local.complete}<Badge variant="outline">已下载</Badge>{/if}
                    {#if advisory?.classificationConfidence}<Badge variant="outline">{advisory.classificationConfidence}</Badge>{/if}
                  </div>
                  <div class="mt-1 flex flex-wrap gap-2 text-xs text-muted-foreground">
                    <span>{advisory?.primaryCategoryCn ?? model.pymss.primary_category}</span>
                    <span>{advisory?.secondaryCategoryCn ?? model.pymss.secondary_category}</span>
                    <span>{model.pymss.model_type ?? model.pymss.architecture}</span>
                    <span>{formatStemTargets(advisory?.targetStem || model.pymss.target_stem)}</span>
                    <span>{formatBytes(model.pymss.size_bytes)}</span>
                  </div>
                  {#if advisory}
                    <div class="mt-2 rounded-sm border border-border bg-muted/35 px-2 py-1.5 text-xs leading-5">
                      <div><span class="font-medium">能力：</span>{advisory.note.ability}</div>
                      <div><span class="font-medium">备注：</span>{advisory.note.usage}</div>
                      <div class="text-muted-foreground"><span class="font-medium text-foreground">体积提示：</span>{advisory.risk}</div>
                    </div>
                  {/if}
                </div>
              </Table.Cell>
              <Table.Cell>
                <div class="flex justify-end gap-1">
                  <Button variant="ghost" size="icon-sm" type="button" onclick={() => onShowDetail(model.id)} aria-label="详情"><Info class="size-4" /></Button>
                  <Button variant="ghost" size="icon-sm" type="button" onclick={() => onDownload(model.id)} disabled={busyAction !== null} aria-label="下载"><Download class="size-4" /></Button>
                  <Button size="sm" type="button" onclick={() => onSetLoadTarget(model.id)} disabled={!model.pymss.supported}>加载</Button>
                </div>
              </Table.Cell>
            </Table.Row>
          {/each}
          {#if filteredModels.length === 0}
            <Table.Row>
              <Table.Cell colspan={3} class="p-6 text-center text-sm text-muted-foreground">没有匹配的模型。</Table.Cell>
            </Table.Row>
          {/if}
        </Table.Body>
      </Table.Root>
    </CardContent>
  </Card>

  {#if selectedCatalog}
    {@const detailAdvisory = getAdvisory(selectedCatalog.id)}
    {@const detailRecommendationLabel = recommendationLabel(detailAdvisory)}
    <Card>
      <CardHeader class="flex-row items-start justify-between">
        <div>
          <CardTitle class="break-words text-xl">{selectedCatalog.id}</CardTitle>
          {#if detailRecommendationLabel}<div class="mt-2"><Badge>{detailRecommendationLabel}</Badge></div>{/if}
          <p class="mt-1 text-sm text-muted-foreground">{selectedCatalog.pymss.aliases.join(", ") || "无别名"}</p>
        </div>
        <Button variant="ghost" size="sm" type="button" onclick={onCloseDetail}>关闭</Button>
      </CardHeader>
      <CardContent>
        {#if detailAdvisory}
          <div class="mb-4 grid gap-3 rounded-sm border border-border bg-muted/35 p-3 text-sm leading-6 md:grid-cols-2">
            <div><span class="font-medium">能力：</span>{detailAdvisory.note.ability}</div>
            <div><span class="font-medium">业务约束：</span>{AUDIO_BUSINESS_REQUIREMENT}</div>
            <div class="md:col-span-2"><span class="font-medium">备注：</span>{detailAdvisory.note.usage}</div>
            <div><span class="font-medium">一级分类：</span>{detailAdvisory.primaryCategoryCn}</div>
            <div><span class="font-medium">二级分类：</span>{detailAdvisory.secondaryCategoryCn}</div>
            <div><span class="font-medium">输出目标：</span>{formatStemTargets(detailAdvisory.targetStem)}</div>
            <div><span class="font-medium">Config instruments：</span>{formatStemTargets(detailAdvisory.configInstruments)}</div>
            <div><span class="font-medium">分类依据：</span>{detailAdvisory.classificationBasis || "-"}</div>
            <div><span class="font-medium">体积提示：</span>{detailAdvisory.risk}</div>
          </div>
        {/if}
        <div class="divide-y divide-border">
          {#each selectedCatalog.pymss.files ?? [] as file}
            <div class="grid gap-2 py-3 text-sm md:grid-cols-[7rem_minmax(0,1fr)_7rem]">
              <span class="text-muted-foreground">{file.role}</span>
              <span class="truncate font-mono text-xs">{file.relpath}</span>
              <span class="text-right">{file.exists ? "已存在" : "缺失"} · {formatBytes(file.size_bytes)}</span>
            </div>
          {/each}
        </div>
      </CardContent>
    </Card>
  {/if}
</section>
