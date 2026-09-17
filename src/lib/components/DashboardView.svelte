<script lang="ts">
  import {
    ArrowRight,
    FileAudio,
    Library,
    SlidersHorizontal,
  } from "@lucide/svelte";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Card, CardContent } from "$lib/components/ui/card/index.js";
  import { formatBytes } from "../params";
  import type {
    DownloadSource,
    HealthResponse,
    LoadedModel,
    ServerInfo,
    View,
  } from "../types";

  export let health: HealthResponse | null;
  export let serverInfo: ServerInfo | null;
  export let downloadSource: DownloadSource | null;
  export let loadedModel: LoadedModel | null;
  export let onSelectView: (view: View) => void;

  const actions = [
    { view: "catalog" as View, label: "浏览模型", icon: Library },
    { view: "loaded" as View, label: "加载模型", icon: SlidersHorizontal },
    { view: "separate" as View, label: "分离音频", icon: FileAudio },
  ];
</script>

<section class="space-y-8">
  <div class="mx-auto max-w-3xl text-center">
    <h1
      class="text-[32px] font-medium leading-tight tracking-normal sm:text-4xl"
    >
      PYMSS Studio 分离
    </h1>
    <p class="mx-auto mt-3 max-w-xl text-base leading-7 text-muted-foreground">
      {loadedModel
        ? loadedModel.id
        : "先加载模型，再从浏览器上传音频进行分离。"}
    </p>
  </div>

  <Card size="sm" class="mx-auto max-w-3xl">
    <CardContent>
      <div
        class="flex flex-col gap-1 font-mono text-sm sm:flex-row sm:items-center sm:justify-between"
      >
        <span>下载源={downloadSource?.source ?? "-"}</span>
        <span>设备={health?.device ?? "-"}</span>
        <span>请求上限={formatBytes(serverInfo?.limits.max_request_bytes ?? 0)}</span>
      </div>
    </CardContent>
  </Card>

  <div class="mx-auto grid max-w-3xl gap-3 md:grid-cols-3">
    {#each actions as action, index}
      <Button
        variant={index === 0 ? "default" : "outline"}
        size="lg"
        class="h-12 justify-between px-4"
        type="button"
        onclick={() => onSelectView(action.view)}
      >
        <svelte:component this={action.icon} class="size-4" />
        {action.label}
        {#if index === 0}
          <ArrowRight class="size-4" />
        {/if}
      </Button>
    {/each}
  </div>
</section>
