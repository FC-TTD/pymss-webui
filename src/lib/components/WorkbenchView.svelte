<script lang="ts">
  import { onDestroy } from "svelte";
  import {
    CheckCircle2,
    Download,
    FileAudio,
    HardDriveDownload,
    Loader2,
    Play,
    Search,
    UploadCloud,
  } from "@lucide/svelte";
  import { Alert, AlertDescription } from "$lib/components/ui/alert/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Card, CardContent, CardHeader, CardTitle } from "$lib/components/ui/card/index.js";
  import { Checkbox } from "$lib/components/ui/checkbox/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import { Label } from "$lib/components/ui/label/index.js";
  import SelectField from "./SelectField.svelte";
  import { base64ToBlob } from "../audio";
  import {
    AUDIO_BUSINESS_REQUIREMENT,
    filterAndSortModels,
    getAdvisory,
    getScenario,
    recommendationLabel,
    scenarioOptions,
    sortOptions,
  } from "../model-selection";
  import { formatBytes } from "../params";
  import { formatStem, formatStemTargets } from "../stem-labels";
  import type {
    CatalogListResponse,
    CatalogModel,
    CatalogQuery,
    LoadedModel,
    OutputAudioFormat,
    SeparationJsonResult,
    SeparationResponseFormat,
  } from "../types";

  export let catalog: CatalogListResponse | null;
  export let loadedModel: LoadedModel | null;
  export let selectedDownloadModels: string[];
  export let catalogQuery: CatalogQuery;
  export let busyAction: string | null;
  export let audioFile: File | null;
  export let selectedStems: string[];
  export let responseFormat: SeparationResponseFormat;
  export let outputAudioFormat: OutputAudioFormat;
  export let resultUrl: string | null;
  export let resultName: string;
  export let jsonResult: SeparationJsonResult | null;
  export let onApplyFilters: () => void;
  export let onDownload: (model: string) => void;
  export let onDownloadSelected: () => void;
  export let onToggleDownloadSelection: (model: string, checked: boolean) => void;
  export let onSetDownloadSelection: (models: string[]) => void;
  export let onLoadModel: (model: string) => void;
  export let onToggleStem: (stem: string, checked: boolean) => void;
  export let onSeparate: () => void;
  export let onDownloadJsonOutput: (output: SeparationJsonResult["outputs"][number]) => void;

  const localOptions = [
    { value: "all", label: "全部" },
    { value: "complete", label: "已下载" },
    { value: "missing", label: "未下载" },
  ];

  const responseOptions = [
    { value: "json", label: "分轨" },
    { value: "zip", label: "zip" },
  ];

  const outputOptions = [
    { value: "wav", label: "wav 48000Hz PCM_24" },
  ];

  const scenarioGroups = [
    { label: "歌曲制作", scenarios: ["vocal", "instrumental", "karaoke", "choir", "breath"] },
    { label: "影视对白", scenarios: ["speech", "dereverb", "spatial"] },
    { label: "降噪清理", scenarios: ["denoise", "restoration"] },
    { label: "分轨编曲", scenarios: ["four_stem", "six_stem", "mega_53"] },
    { label: "乐器提取", scenarios: ["drums", "single_instrument"] },
  ].map((group) => ({
    ...group,
    options: group.scenarios
      .map((id) => scenarioOptions.find((scenario) => scenario.value === id))
      .filter((scenario): scenario is (typeof scenarioOptions)[number] => Boolean(scenario)),
  }));

  let selectedModelId = "";
  let previewUrls: Array<{ stem: string; url: string }> = [];
  let lastJsonResult: SeparationJsonResult | null = null;

  $: activeScenario = getScenario(catalogQuery.scenario);
  $: filteredModels = filterAndSortModels(catalog?.data ?? [], catalogQuery);
  $: if (filteredModels.length && !filteredModels.some((model) => model.id === selectedModelId)) {
    selectedModelId = filteredModels.find((model) => model.id === loadedModel?.id)?.id ?? filteredModels[0].id;
  }
  $: selectedModel = filteredModels.find((model) => model.id === selectedModelId) ?? null;
  $: selectedAdvisory = selectedModel ? getAdvisory(selectedModel.id) : null;
  $: selectedRecommendationLabel = recommendationLabel(selectedAdvisory);
  $: loadedAdvisory = loadedModel ? getAdvisory(loadedModel.id) : null;
  $: loadedRecommendationLabel = recommendationLabel(loadedAdvisory);
  $: loadedCatalogModel = loadedModel
    ? (catalog?.data ?? []).find((model) =>
        [loadedModel.id, loadedModel.pymss.catalog_name, loadedModel.pymss.catalog_target_stem].includes(model.id) ||
        model.pymss.name === loadedModel.id ||
        model.pymss.aliases.includes(loadedModel.id),
      ) ?? null
    : null;
  $: visibleModels = filteredModels.map((model) => model.id);
  $: allVisibleSelected = visibleModels.length > 0 && visibleModels.every((model) => selectedDownloadModels.includes(model));

  $: {
    if (jsonResult !== lastJsonResult) {
      for (const item of previewUrls) {
        URL.revokeObjectURL(item.url);
      }
      previewUrls = jsonResult
        ? jsonResult.outputs.map((output) => ({
            stem: output.stem,
            url: URL.createObjectURL(base64ToBlob(output.audio.data, "audio/wav")),
          }))
        : [];
      lastJsonResult = jsonResult;
    }
  }

  onDestroy(() => {
    for (const item of previewUrls) {
      URL.revokeObjectURL(item.url);
    }
  });

  function setVisibleSelection(checked: boolean): void {
    if (checked) {
      onSetDownloadSelection([...selectedDownloadModels, ...visibleModels]);
    } else {
      onSetDownloadSelection(selectedDownloadModels.filter((model) => !visibleModels.includes(model)));
    }
  }

  function previewUrlFor(stem: string): string | null {
    return previewUrls.find((item) => item.stem === stem)?.url ?? null;
  }

  function selectModel(model: CatalogModel): void {
    selectedModelId = model.id;
  }

  function selectScenario(value: string): void {
    catalogQuery.selectionMode = "scenario";
    catalogQuery.scenario = value;
    catalogQuery.sort = "recommended";
  }

  function handleModelRowKey(event: KeyboardEvent, model: CatalogModel): void {
    if (event.key !== "Enter" && event.key !== " ") {
      return;
    }
    event.preventDefault();
    selectModel(model);
  }

  function loadSelectedModel(): void {
    if (selectedModel) {
      onLoadModel(selectedModel.id);
    }
  }

  function applyFilters(event: SubmitEvent): void {
    event.preventDefault();
    onApplyFilters();
  }

  function separate(event: SubmitEvent): void {
    event.preventDefault();
    onSeparate();
  }
</script>

<section class="text-[15px]">
  <div class="grid gap-4 xl:grid-cols-[minmax(25rem,0.92fr)_minmax(0,1.28fr)]">
    <aside class="overflow-hidden rounded-[4px] border border-[#7f8fa6] bg-[#f8fafc] shadow-[0_1px_3px_rgba(15,23,42,0.16)]">
      <div class="border-b border-[#7f8fa6] bg-[#344e73] px-4 py-3 text-white">
        <div class="flex items-center justify-between gap-3">
          <div>
            <div class="flex items-center gap-2 text-lg font-semibold">
              <FileAudio class="size-5 text-blue-100" />
              模型选择控制台
            </div>
            <div class="mt-0.5 text-[13px] text-blue-100">{activeScenario.label} · {filteredModels.length} / {catalog?.pymss.total ?? 0}</div>
          </div>
          <Button
            variant="outline"
            size="sm"
            type="button"
            onclick={onDownloadSelected}
            disabled={busyAction !== null || !selectedDownloadModels.length}
            class="border-blue-200/60 bg-slate-900/20 text-white hover:bg-slate-800 hover:text-white"
          >
            {#if busyAction === "download"}
              <Loader2 class="size-4 animate-spin" />
            {:else}
              <HardDriveDownload class="size-4" />
            {/if}
            批量（{selectedDownloadModels.length}）
          </Button>
        </div>
      </div>

      <div class="border-b border-[#c9d4e5] bg-white px-4 py-3">
        <div class="grid gap-2 text-[13px] leading-5 text-slate-700 sm:grid-cols-4">
          <div class="border-l-2 border-[#1f5fbd] pl-2">
            <div class="font-semibold text-slate-950">1. 选场景</div>
            <div>按人声、伴奏、降噪或分轨用途筛选模型。</div>
          </div>
          <div class="border-l-2 border-[#8fb2e3] pl-2">
            <div class="font-semibold text-slate-950">2. 选模型</div>
            <div>查看输出目标、体积和 SDR 备注，确认是否已下载。</div>
          </div>
          <div class="border-l-2 border-[#8fb2e3] pl-2">
            <div class="font-semibold text-slate-950">3. 加载确认</div>
            <div>点“加载选中模型”，右侧出现“当前使用”后再继续。</div>
          </div>
          <div class="border-l-2 border-[#8fb2e3] pl-2">
            <div class="font-semibold text-slate-950">4. 上传分离</div>
            <div>选择输出 Stem，上传音频，生成预览和下载文件。</div>
          </div>
        </div>
      </div>

      <form class="border-b border-[#c9d4e5] bg-[#f7f9fc] p-4 text-[14px]" onsubmit={applyFilters}>
        <div class="grid gap-2">
          <Label>业务场景</Label>
          <div class="space-y-2">
            {#each scenarioGroups as group}
              <div class="grid grid-cols-[4.5rem_minmax(0,1fr)] items-start gap-2">
                <div class="pt-1 text-[12px] font-semibold text-[#344e73]">{group.label}</div>
                <div class="flex flex-wrap gap-1.5">
                  {#each group.options as scenario}
                    <button
                      type="button"
                      class={`h-8 rounded-[3px] border px-3 text-[13px] font-medium transition ${catalogQuery.scenario === scenario.value ? "border-[#1d5fbf] bg-[#1f5fbd] text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.25)]" : "border-[#d5dce8] bg-white text-slate-700 hover:border-[#9fb3d0]"}`}
                      onclick={() => selectScenario(scenario.value)}
                    >
                      {scenario.label}
                    </button>
                  {/each}
                </div>
              </div>
            {/each}
          </div>
        </div>

        <div class="mt-4 grid gap-3 md:grid-cols-[minmax(0,1fr)_8.5rem_7.5rem]">
          <div class="grid gap-1.5">
            <Label for="workbench-search">搜索模型</Label>
            <div class="relative">
              <Search class="pointer-events-none absolute left-2.5 top-2.5 size-4 text-slate-400" />
              <Input id="workbench-search" class="h-10 rounded-[3px] border-[#cfd8e6] bg-white pl-8 text-[14px]" bind:value={catalogQuery.q} placeholder="输入模型名 / 备注 / stem" />
            </div>
          </div>
          <SelectField
            id="workbench-local"
            label="本地状态"
            value={catalogQuery.local}
            options={localOptions}
            onValueChange={(value) => (catalogQuery.local = value as CatalogQuery["local"])}
          />
          <SelectField
            id="workbench-sort"
            label="排序"
            value={catalogQuery.sort}
            options={sortOptions}
            onValueChange={(value) => (catalogQuery.sort = value as CatalogQuery["sort"])}
          />
        </div>

        <div class="mt-3 flex flex-wrap items-center gap-3 text-[13px]">
          <label class="flex h-8 items-center gap-2">
            <Checkbox bind:checked={catalogQuery.recommendedOnly} />
            <span>仅看推荐</span>
          </label>
          <label class="ml-auto flex h-8 items-center gap-2">
            <span>选择当前结果</span>
            <Checkbox checked={allVisibleSelected} onCheckedChange={(checked) => setVisibleSelection(checked === true)} />
          </label>
          <Button class="bg-white" variant="outline" size="sm" type="submit" disabled={busyAction !== null}>
            {#if busyAction === "catalog"}<Loader2 class="size-4 animate-spin" />{/if}
            刷新
          </Button>
        </div>
      </form>

      <div class="border-b border-[#c9d4e5] bg-[#f8fbff] p-4">
        {#if selectedModel}
          <div class="rounded-[4px] border border-[#8fb2e3] bg-[#eaf3ff] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)]">
            <div class="flex gap-3">
              <div class="mt-1 flex size-12 shrink-0 items-center justify-center rounded-full bg-[#1f5fbd] text-white shadow-sm">
                <FileAudio class="size-6" />
              </div>
              <div class="min-w-0 flex-1">
                <div class="flex items-start justify-between gap-2">
                  <div class="break-all text-[15px] font-semibold leading-5 text-slate-950">{selectedModel.id}</div>
                  <div class="flex shrink-0 flex-wrap justify-end gap-1.5">
                    {#if selectedModel.id === loadedModel?.id}<Badge>当前已加载</Badge>{/if}
                    {#if selectedRecommendationLabel}<Badge variant="outline" class="bg-white">{selectedRecommendationLabel}</Badge>{/if}
                    {#if selectedModel.pymss.local.complete}<Badge variant="outline" class="bg-white">已下载</Badge>{/if}
                  </div>
                </div>
                <div class="mt-3 grid gap-x-5 gap-y-1.5 text-[12px] leading-5 text-slate-700 sm:grid-cols-2">
                  <div><span class="font-medium text-slate-950">输出目标</span>　{formatStemTargets(selectedAdvisory?.targetStem || selectedModel.pymss.target_stem)}</div>
                  <div><span class="font-medium text-slate-950">体积</span>　{formatBytes(selectedModel.pymss.size_bytes)}</div>
                  <div><span class="font-medium text-slate-950">配置</span>　{selectedModel.pymss.primary_category} / {selectedModel.pymss.secondary_category}</div>
                  {#if selectedAdvisory}
                    <div><span class="font-medium text-slate-950">备注</span>　{selectedAdvisory.note.usage}</div>
                  {/if}
                </div>
              </div>
            </div>
            <div class="mt-3 border-t border-[#9bbbe8] pt-3">
              <div class="grid gap-2 sm:grid-cols-[minmax(0,1fr)_8.5rem]">
                <Button type="button" onclick={loadSelectedModel} disabled={busyAction !== null || !selectedModel.pymss.supported} class="h-9 rounded-[3px] bg-[#1f5fbd]">
                {#if busyAction === "load"}<Loader2 class="size-4 animate-spin" />{:else}<CheckCircle2 class="size-4" />{/if}
                加载选中模型
                </Button>
                <Button variant="outline" type="button" onclick={() => onDownload(selectedModel.id)} disabled={busyAction !== null} class="h-9 rounded-[3px] border-[#7aa2d8] bg-white text-[#144d95]">
                  {#if busyAction === "download"}<Loader2 class="size-4 animate-spin" />{:else}<Download class="size-4" />{/if}
                  下载模型
                </Button>
              </div>
            </div>
          </div>
        {:else}
          <Alert>
            <FileAudio class="size-5" />
            <AlertDescription>先在下方选择一个模型。</AlertDescription>
          </Alert>
        {/if}
      </div>

      <div class="flex items-center justify-between gap-3 border-b border-[#c9d4e5] bg-white px-4 py-2.5">
        <div class="text-[13px] text-slate-700">共找到 <span class="font-semibold text-slate-950">{filteredModels.length}</span> 个模型</div>
        <button type="button" class="text-[12px] font-medium text-[#1f5fbd]" onclick={onApplyFilters}>刷新列表</button>
      </div>
      <div class="max-h-[39rem] overflow-y-auto bg-white">
        <div class="grid grid-cols-[minmax(13rem,1fr)_8.5rem_5rem_5rem] border-b border-[#d7deea] bg-[#f4f7fb] px-3 py-2 text-[12px] font-semibold text-slate-600">
          <div>模型名称</div>
          <div>输出目标</div>
          <div>体积</div>
          <div>状态</div>
        </div>
        {#each filteredModels as model}
          {@const advisory = getAdvisory(model.id)}
          {@const modelRecommendationLabel = recommendationLabel(advisory)}
          {@const active = selectedModelId === model.id}
          <div
            role="button"
            tabindex="0"
            class={`w-full border-b px-3 py-3 text-left transition-colors ${active ? "border-blue-300 shadow-[inset_3px_0_0_#2563eb]" : "border-slate-200 bg-white hover:bg-slate-50"}`}
            style={active ? "background-color:#e7f0ff;border-bottom-color:#93c5fd;" : ""}
            onclick={() => selectModel(model)}
            onkeydown={(event) => handleModelRowKey(event, model)}
          >
            <div class="grid grid-cols-[minmax(13rem,1fr)_8.5rem_5rem_5rem] grid-rows-[auto_auto] text-[12px]">
              <div class="row-span-2 flex min-w-0 items-center gap-2 border-r border-slate-100 pr-3">
                <span
                  class={`flex size-4 shrink-0 items-center justify-center rounded-full border ${active ? "border-blue-600 bg-blue-600 ring-2 ring-blue-100" : "border-slate-300 bg-white"}`}
                  aria-hidden="true"
                >
                  {#if active}<span class="size-1.5 rounded-full bg-white"></span>{/if}
                </span>
                <div class="min-w-0">
                  <div class="line-clamp-2 break-all text-[13px] font-medium leading-4 text-slate-950">{model.id}</div>
                  <div class="mt-1 flex flex-wrap gap-1">
                    {#if modelRecommendationLabel}<Badge>{modelRecommendationLabel}</Badge>{/if}
                    {#if loadedModel?.id === model.id}<Badge variant="outline" class="bg-white">当前加载</Badge>{/if}
                    <label class="inline-flex h-5 items-center gap-1 rounded-[3px] border border-slate-200 bg-white px-1.5 text-[11px] text-slate-500">
                      <Checkbox
                        checked={selectedDownloadModels.includes(model.id)}
                        onCheckedChange={(checked) => onToggleDownloadSelection(model.id, checked === true)}
                        onclick={(event) => event.stopPropagation()}
                        aria-label={`加入批量下载 ${model.id}`}
                      />
                      批量
                    </label>
                  </div>
                </div>
              </div>
              <div class="px-3 pb-2 text-slate-700 leading-4">{formatStemTargets(advisory?.targetStem || model.pymss.target_stem)}</div>
              <div class="px-3 pb-2 text-slate-600">{formatBytes(model.pymss.size_bytes)}</div>
              <div class="px-3 pb-2">
                {#if model.pymss.local.complete}
                  <span class="inline-flex rounded-[3px] border border-[#a8c5f2] bg-[#eaf3ff] px-2 py-0.5 text-[11px] font-medium text-[#1f5fbd]">已下载</span>
                {:else}
                  <span class="inline-flex rounded-[3px] border border-slate-300 bg-white px-2 py-0.5 text-[11px] text-slate-600">未下载</span>
                {/if}
              </div>
              <div class="col-span-3 border-t border-slate-100 px-3 pt-2 text-[12px] leading-5 text-slate-600">
                <span class="font-semibold text-slate-700">备注 / SDR：</span>{advisory?.note.usage ?? advisory?.note.ability ?? "-"}
              </div>
            </div>
          </div>
        {/each}
        {#if filteredModels.length === 0}
          <div class="p-6 text-center text-base text-slate-500">没有匹配的模型。</div>
        {/if}
      </div>
    </aside>

    <div class="overflow-hidden rounded-[4px] border border-[#7f8fa6] bg-[#f8fbff] shadow-[0_1px_3px_rgba(15,23,42,0.16)]">
      <div class="border-b border-[#7f8fa6] bg-[#344e73] px-5 py-4 text-white">
        <h2 class="text-xl font-semibold text-white">分离任务工作区</h2>
        <p class="mt-1 text-[13px] leading-5 text-blue-100">
          {loadedModel ? `当前使用 ${loadedModel.id} · ${loadedModel.pymss.sample_rate} Hz` : "加载模型后即可选择轨道并上传音频。"}
        </p>
      </div>

      <div class="space-y-3 p-3">
        <section class="rounded-[4px] border border-[#c6d5ea] bg-[#eef5ff] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)]">
          <div class="border-b border-[#8aa8cf] pb-2">
            <h3 class="text-base font-semibold text-[#12365b]">1. 当前已加载模型</h3>
          </div>
          <div class="pt-3">
            {#if loadedModel}
              <div class="rounded-[3px] border border-[#d9e2ef] bg-white px-4 py-4 shadow-sm">
                <div class="flex gap-5">
                  <div class="flex size-20 shrink-0 items-center justify-center rounded-full bg-[#285fa9] text-white shadow-sm">
                    <FileAudio class="size-10" />
                  </div>
                  <div class="min-w-0 flex-1">
                    <div class="flex flex-wrap items-center gap-2">
                      <span class="break-all text-lg font-semibold text-slate-950">{loadedModel.id}</span>
                      <Badge>当前使用</Badge>
                      {#if loadedRecommendationLabel}<Badge variant="outline" class="bg-white">{loadedRecommendationLabel}</Badge>{/if}
                    </div>
                    {#if loadedAdvisory}
                      <div class="mt-3 grid gap-x-10 gap-y-2 text-[13px] leading-5 text-slate-700 md:grid-cols-3">
                        <div><span class="font-medium text-slate-950">输出目标</span>　{formatStemTargets(loadedAdvisory.targetStem || loadedModel.pymss.catalog_target_stem)}</div>
                        <div><span class="font-medium text-slate-950">体积</span>　{formatBytes(loadedCatalogModel?.pymss.size_bytes ?? 0)}</div>
                        <div><span class="font-medium text-slate-950">采样率</span>　{loadedModel.pymss.sample_rate} Hz</div>
                        <div><span class="font-medium text-slate-950">配置</span>　{loadedModel.pymss.instruments.map(formatStem).join(" | ")}</div>
                        <div class="md:col-span-2"><span class="font-medium text-slate-950">备注</span>　{loadedAdvisory.note.usage}</div>
                      </div>
                    {/if}
                  </div>
                </div>
              </div>
            {:else}
              <Alert>
                <FileAudio class="size-5" />
                <AlertDescription>左侧加载一个模型后开始处理。</AlertDescription>
              </Alert>
            {/if}
          </div>
        </section>

        <form onsubmit={separate}>
          <div class="grid gap-3 lg:grid-cols-[minmax(16rem,0.75fr)_minmax(0,1.55fr)]">
            <section class="rounded-[4px] border border-[#c6d5ea] bg-white shadow-sm">
              <div class="border-b border-[#d9e2ef] bg-[#f2f7ff] px-4 py-3">
                <h3 class="text-base font-semibold text-[#12365b]">2. 选择输出 Stem</h3>
              </div>
              <div class="p-4">
                <div class="space-y-2 rounded-[3px] border border-[#d9e2ef] bg-white p-3">
                  {#each loadedModel?.pymss.instruments ?? [] as stem}
                    <div class="flex h-8 items-center gap-2">
                      <Checkbox
                        id={`workbench-stem-${stem}`}
                        checked={selectedStems.includes(stem)}
                        onCheckedChange={(checked) => onToggleStem(stem, checked)}
                      />
                      <Label for={`workbench-stem-${stem}`} class="text-[14px] font-medium">{formatStem(stem)}</Label>
                    </div>
                  {/each}
                  {#if !loadedModel}
                    <span class="text-[14px] text-slate-500">暂无已加载模型。</span>
                  {/if}
                </div>
              </div>
            </section>

            <section class="rounded-[4px] border border-[#c6d5ea] bg-white shadow-sm">
              <div class="border-b border-[#d9e2ef] bg-[#f2f7ff] px-4 py-3">
                <h3 class="text-base font-semibold text-[#12365b]">3. 上传音频</h3>
              </div>
              <div class="p-4">
                <label for="workbench-audio-file" class="flex min-h-40 cursor-pointer flex-col items-center justify-center rounded-[3px] border border-dashed border-[#b7c4d6] bg-[#fbfdff] px-4 py-6 text-center transition hover:border-[#7fa5d9] hover:bg-[#f5f9ff]">
                  <UploadCloud class="size-8 text-[#285fa9]" />
                  <span class="mt-3 text-[14px] font-medium text-slate-700">点击选择音频文件</span>
                  <span class="mt-1 text-[12px] text-slate-500">支持 wav / flac / mp3 / m4a / ogg</span>
                  {#if audioFile}
                    <span class="mt-4 w-full rounded-[3px] border border-[#d9e2ef] bg-white px-3 py-2 text-left text-[13px] text-slate-700">
                      {audioFile.name} · {formatBytes(audioFile.size)}
                    </span>
                  {/if}
                </label>
                <input
                  id="workbench-audio-file"
                  type="file"
                  accept="audio/*"
                  class="sr-only"
                  onchange={(event) => (audioFile = (event.currentTarget as HTMLInputElement).files?.[0] ?? null)}
                />
              </div>
            </section>
          </div>

          <section class="bg-white">
            <div class="border-b border-slate-200 bg-[#eef5fc] px-5 py-3">
              <h3 class="text-base font-semibold text-[#12365b]">4. 响应格式</h3>
            </div>
            <div class="space-y-3 p-5">
              <div class="grid gap-3 md:grid-cols-2">
                <SelectField
                  id="workbench-response-format"
                  label="响应格式"
                  value={responseFormat}
                  options={responseOptions}
                  onValueChange={(value) => (responseFormat = value as SeparationResponseFormat)}
                />
                <SelectField
                  id="workbench-output-format"
                  label="音频格式"
                  value={outputAudioFormat}
                  options={outputOptions}
                  disabled
                  onValueChange={(value) => (outputAudioFormat = value as OutputAudioFormat)}
                />
              </div>
              <div class="border border-slate-200 bg-[#f6f9fc] p-3 text-sm leading-6 text-slate-600">
                分轨模式会在结果区逐条预览和下载 WAV；zip 模式会把所有已选 stem 打包下载。两种模式都是 48000Hz PCM_24 WAV。
              </div>
            </div>
          </section>

          <section class="bg-[#f9fbfd]">
            <div class="flex flex-col gap-3 border-b border-slate-200 bg-[#eef5fc] px-5 py-3 md:flex-row md:items-center md:justify-between">
              <h3 class="text-base font-semibold text-[#12365b]">5. 轨道预览与下载</h3>
              <Button type="submit" disabled={busyAction !== null || !loadedModel}>
                {#if busyAction === "separate"}
                  <Loader2 class="size-4 animate-spin" />
                {:else}
                  <Play class="size-4" />
                {/if}
                开始分离
              </Button>
            </div>
            <div class="p-5">
              {#if resultUrl}
                <Button class="w-full" href={resultUrl} download={resultName}>
                  <Download class="size-4" /> 下载 ZIP
                </Button>
              {:else if jsonResult}
                <div class="space-y-3">
                  <div class="text-[14px] text-slate-600">{jsonResult.metadata.input_seconds.toFixed(1)} 秒 · {jsonResult.outputs.length} 个输出</div>
                  {#each jsonResult.outputs as output}
                    <div class="space-y-2 border border-slate-300 bg-white p-3">
                      <div class="flex items-center justify-between gap-2 text-[14px]">
                        <span class="font-medium text-slate-950">{formatStem(output.stem)}</span>
                        <Button variant="outline" size="sm" type="button" onclick={() => onDownloadJsonOutput(output)}>
                          <Download class="size-4" />
                          下载
                        </Button>
                      </div>
                      {#if previewUrlFor(output.stem)}
                        <audio class="w-full" controls src={previewUrlFor(output.stem) ?? undefined}></audio>
                      {/if}
                    </div>
                  {/each}
                </div>
              {:else}
                <Alert>
                  <UploadCloud class="size-5" />
                  <AlertDescription>暂无结果。</AlertDescription>
                </Alert>
              {/if}
            </div>
          </section>
        </form>
      </div>
    </div>
  </div>
</section>
