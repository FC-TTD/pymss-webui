<script lang="ts">
  import { Info, Loader2 } from "@lucide/svelte";
  import { Alert, AlertDescription } from "$lib/components/ui/alert/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Card, CardContent, CardHeader, CardTitle } from "$lib/components/ui/card/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import { Label } from "$lib/components/ui/label/index.js";
  import { Textarea } from "$lib/components/ui/textarea/index.js";
  import SelectField from "./SelectField.svelte";
  import { AUDIO_BUSINESS_REQUIREMENT, getAdvisory, recommendationLabel } from "../model-selection";
  import { formatStem, formatStemTargets } from "../stem-labels";
  import type { DownloadSourceName, LoadedModel } from "../types";

  export let loadedModel: LoadedModel | null;
  export let busyAction: string | null;
  export let loadModelName: string;
  export let loadSourceOverride: DownloadSourceName | "";
  export let loadEndpointOverride: string;
  export let inferenceParamsText: string;
  export let onLoad: () => void;

  const sourceOptions = [
    { value: "", label: "当前默认" },
    { value: "modelscope", label: "modelscope" },
    { value: "huggingface", label: "huggingface" },
    { value: "hf-mirror", label: "hf-mirror" },
  ];

  $: advisory = loadedModel ? getAdvisory(loadedModel.id) : null;
  $: advisoryRecommendationLabel = recommendationLabel(advisory);
</script>

<section class="grid gap-8 xl:grid-cols-[minmax(0,1fr)_22rem]">
  <div class="space-y-5">
    <div>
      <h1 class="text-[30px] font-medium leading-tight tracking-normal">已加载模型</h1>
      <p class="mt-2 text-sm text-muted-foreground">
        {loadedModel ? `${loadedModel.pymss.sample_rate} Hz · ${loadedModel.pymss.category} · ${AUDIO_BUSINESS_REQUIREMENT}` : "当前还没有加载模型。"}
      </p>
    </div>

    <Card>
      <CardContent>
      {#if loadedModel}
        <h2 class="break-words text-xl font-medium">{loadedModel.id}</h2>
        {#if advisoryRecommendationLabel}<div class="mt-2"><Badge>{advisoryRecommendationLabel}</Badge></div>{/if}
        {#if advisory}
          <div class="mt-3 rounded-sm border border-border bg-muted/35 p-3 text-sm leading-6">
            <div><span class="font-medium">能力：</span>{advisory.note.ability}</div>
            <div><span class="font-medium">备注：</span>{advisory.note.usage}</div>
            <div class="text-muted-foreground"><span class="font-medium text-foreground">输出目标：</span>{formatStemTargets(advisory.targetStem || loadedModel.pymss.catalog_target_stem)}</div>
            <div class="text-muted-foreground"><span class="font-medium text-foreground">体积提示：</span>{advisory.risk}</div>
          </div>
        {/if}
        <div class="mt-4 flex flex-wrap gap-2">
          {#each loadedModel.pymss.instruments as stem}
            <Badge variant="outline">{formatStem(stem)}</Badge>
          {/each}
        </div>
        <div class="mt-6 divide-y divide-border text-sm">
          <div class="flex justify-between gap-4 py-3">
            <span class="text-muted-foreground">类型</span>
            <span>{loadedModel.pymss.model_type ?? loadedModel.pymss.architecture}</span>
          </div>
          <div class="flex justify-between gap-4 py-3">
            <span class="text-muted-foreground">参数</span>
            <span class="text-right">{Object.keys(loadedModel.pymss.supported_parameters).join(", ") || "-"}</span>
          </div>
        </div>
      {:else}
        <Alert>
          <Info class="size-5" />
          <AlertDescription>请从模型目录选择，或手动输入模型别名。</AlertDescription>
        </Alert>
      {/if}
      </CardContent>
    </Card>
  </div>

  <Card>
    <CardHeader>
      <CardTitle>加载</CardTitle>
    </CardHeader>
    <CardContent>
    <form class="space-y-4" on:submit|preventDefault={onLoad}>
      <div class="grid gap-1.5">
        <Label for="load-model">模型</Label>
        <Input id="load-model" class="h-9 text-sm" bind:value={loadModelName} placeholder="bs_roformer_voc_hyperacev2" />
      </div>
      <SelectField
        id="load-source"
        label="下载源"
        value={loadSourceOverride}
        options={sourceOptions}
        onValueChange={(value) => (loadSourceOverride = value as DownloadSourceName | "")}
      />
      <div class="grid gap-1.5">
        <Label for="load-endpoint">端点</Label>
        <Input id="load-endpoint" class="h-9 text-sm" bind:value={loadEndpointOverride} placeholder="可选" />
      </div>
      <div class="grid gap-1.5">
        <Label for="inference-params">推理参数</Label>
        <Textarea id="inference-params" class="min-h-28 font-mono text-sm" bind:value={inferenceParamsText} placeholder={"batch_size=2\nnormalize=true"} />
      </div>
      <Button class="w-full" type="submit" disabled={busyAction !== null}>
        {#if busyAction === "load"}
          <Loader2 class="size-4 animate-spin" />
        {/if}
        加载
      </Button>
    </form>
    </CardContent>
  </Card>
</section>
