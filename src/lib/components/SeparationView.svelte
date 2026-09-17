<script lang="ts">
  import { onDestroy } from "svelte";
  import { Download, Loader2, Play, UploadCloud } from "@lucide/svelte";
  import { Alert, AlertDescription } from "$lib/components/ui/alert/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Card, CardContent, CardHeader, CardTitle } from "$lib/components/ui/card/index.js";
  import { Checkbox } from "$lib/components/ui/checkbox/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import { Label } from "$lib/components/ui/label/index.js";
  import SelectField from "./SelectField.svelte";
  import { base64ToBlob } from "../audio";
  import { AUDIO_BUSINESS_REQUIREMENT, getAdvisory, recommendationLabel } from "../model-selection";
  import { formatStem, formatStemTargets } from "../stem-labels";
  import type { LoadedModel, OutputAudioFormat, SeparationJsonResult, SeparationResponseFormat } from "../types";

  export let loadedModel: LoadedModel | null;
  export let busyAction: string | null;
  export let audioFile: File | null;
  export let selectedStems: string[];
  export let responseFormat: SeparationResponseFormat;
  export let outputAudioFormat: OutputAudioFormat;
  export let resultUrl: string | null;
  export let resultName: string;
  export let jsonResult: SeparationJsonResult | null;
  export let onToggleStem: (stem: string, checked: boolean) => void;
  export let onSeparate: () => void;
  export let onDownloadJsonOutput: (output: SeparationJsonResult["outputs"][number]) => void;

  const responseOptions = [
    { value: "json", label: "分轨" },
    { value: "zip", label: "zip" },
  ];

  const outputOptions = [
    { value: "wav", label: "wav 48000Hz PCM_24" },
  ];

  let previewUrls: Array<{ stem: string; url: string }> = [];
  let lastJsonResult: SeparationJsonResult | null = null;

  $: advisory = loadedModel ? getAdvisory(loadedModel.id) : null;
  $: advisoryRecommendationLabel = recommendationLabel(advisory);
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

  function previewUrlFor(stem: string): string | null {
    return previewUrls.find((item) => item.stem === stem)?.url ?? null;
  }
</script>

<section class="grid gap-8 xl:grid-cols-[minmax(0,1fr)_22rem]">
  <div class="space-y-5">
    <div>
      <h1 class="text-[30px] font-medium leading-tight tracking-normal">分离音频</h1>
      <p class="mt-2 text-sm text-muted-foreground">
        {loadedModel ? `当前使用 ${loadedModel.id} · ${AUDIO_BUSINESS_REQUIREMENT}` : "请先加载模型，再运行分离。"}
      </p>
    </div>

    {#if advisory}
      <Card>
        <CardContent>
          <div class="text-sm leading-6">
            {#if advisoryRecommendationLabel}<div class="mb-2"><Badge>{advisoryRecommendationLabel}</Badge></div>{/if}
            <div><span class="font-medium">能力：</span>{advisory.note.ability}</div>
            <div><span class="font-medium">备注：</span>{advisory.note.usage}</div>
            <div class="text-muted-foreground"><span class="font-medium text-foreground">输出目标：</span>{formatStemTargets(advisory.targetStem || loadedModel?.pymss.catalog_target_stem)}</div>
          </div>
        </CardContent>
      </Card>
    {/if}

    <Card>
      <CardContent>
      <form class="space-y-5" on:submit|preventDefault={onSeparate}>
        <div class="grid gap-1.5">
          <Label for="audio-file">音频文件</Label>
          <Input
            id="audio-file"
            type="file"
            accept="audio/*"
            onchange={(event) => (audioFile = (event.currentTarget as HTMLInputElement).files?.[0] ?? null)}
          />
        </div>

        <div>
          <div class="mb-2 text-sm font-medium">输出轨道</div>
          <div class="flex flex-wrap gap-2">
            {#each loadedModel?.pymss.instruments ?? [] as stem}
              <div class="flex h-8 items-center gap-2 border border-input px-2.5">
                <Checkbox
                  id={`stem-${stem}`}
                  checked={selectedStems.includes(stem)}
                  onCheckedChange={(checked) => onToggleStem(stem, checked)}
                />
                <Label for={`stem-${stem}`} class="text-sm">{formatStem(stem)}</Label>
              </div>
            {/each}
          </div>
        </div>

        <div class="grid gap-3 md:grid-cols-2">
          <SelectField
            id="response-format"
            label="响应格式"
            value={responseFormat}
            options={responseOptions}
            onValueChange={(value) => (responseFormat = value as SeparationResponseFormat)}
          />
          <SelectField
            id="output-format"
            label="音频格式"
            value={outputAudioFormat}
            options={outputOptions}
            disabled
            onValueChange={(value) => (outputAudioFormat = value as OutputAudioFormat)}
          />
        </div>
        <div class="text-xs leading-5 text-muted-foreground">
          分轨模式会在结果区逐条预览和下载 WAV；zip 模式会把所有已选 stem 打包下载。两种模式都是 48000Hz PCM_24 WAV。
        </div>

        <Button type="submit" disabled={busyAction !== null || !loadedModel}>
          {#if busyAction === "separate"}
            <Loader2 class="size-4 animate-spin" />
          {:else}
            <Play class="size-4" />
          {/if}
          开始分离
        </Button>
      </form>
      </CardContent>
    </Card>
  </div>

  <Card>
    <CardHeader>
      <CardTitle>结果</CardTitle>
    </CardHeader>
    <CardContent>
    {#if resultUrl}
      <Button class="w-full" href={resultUrl} download={resultName}>
        <Download class="size-4" /> 下载 ZIP
      </Button>
    {:else if jsonResult}
      <div class="space-y-3">
        <div class="text-sm text-muted-foreground">{jsonResult.metadata.input_seconds.toFixed(1)} 秒 · {jsonResult.outputs.length} 个输出</div>
        {#each jsonResult.outputs as output}
          <div class="space-y-2 rounded-sm border border-border p-2">
            <div class="flex items-center justify-between gap-2 text-sm">
              <span class="font-medium">{formatStem(output.stem)}</span>
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
    </CardContent>
  </Card>
</section>
