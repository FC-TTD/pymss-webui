<script lang="ts">
  import { Loader2 } from "@lucide/svelte";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Card, CardContent, CardHeader, CardTitle } from "$lib/components/ui/card/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import { Label } from "$lib/components/ui/label/index.js";
  import SelectField from "./SelectField.svelte";
  import { formatBytes } from "../params";
  import type { DownloadSourceName, ServerInfo, Theme } from "../types";

  export let serverInfo: ServerInfo | null;
  export let busyAction: string | null;
  export let token: string;
  export let theme: Theme;
  export let downloadSourceForm: DownloadSourceName;
  export let downloadEndpointForm: string;
  export let onSaveDownloadSource: () => void;
  export let onOpenToken: () => void;
  export let onClearToken: () => void;
  export let onThemeChange: (theme: Theme) => void;

  const sourceOptions = [
    { value: "modelscope", label: "modelscope" },
    { value: "huggingface", label: "huggingface" },
    { value: "hf-mirror", label: "hf-mirror" },
  ];

  const themeOptions = [
    { value: "light", label: "浅色" },
    { value: "dark", label: "深色" },
  ];
</script>

<section class="space-y-8">
  <div>
    <h1 class="text-[30px] font-medium leading-tight tracking-normal">设置</h1>
    <p class="mt-2 text-sm text-muted-foreground">下载源、访问令牌和运行限制。</p>
  </div>

  <div class="grid gap-6 xl:grid-cols-2">
    <Card>
      <CardHeader>
        <CardTitle>下载源</CardTitle>
      </CardHeader>
      <CardContent>
      <form class="space-y-4" on:submit|preventDefault={onSaveDownloadSource}>
        <SelectField
          id="settings-source"
          label="来源"
          value={downloadSourceForm}
          options={sourceOptions}
          onValueChange={(value) => (downloadSourceForm = value as DownloadSourceName)}
        />
        <div class="grid gap-1.5">
          <Label for="settings-endpoint">端点</Label>
          <Input id="settings-endpoint" class="h-9 text-sm" bind:value={downloadEndpointForm} placeholder="可选" />
        </div>
        <Button type="submit" disabled={busyAction !== null}>
          {#if busyAction === "source"}
            <Loader2 class="size-4 animate-spin" />
          {/if}
          保存
        </Button>
      </form>
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>访问</CardTitle>
      </CardHeader>
      <CardContent>
      <div class="space-y-4">
        <div class="flex items-center justify-between gap-3">
          <span class="text-sm text-muted-foreground">API 令牌</span>
          <Badge variant="outline">{token ? "已保存" : "空"}</Badge>
        </div>
        <div class="flex flex-wrap gap-2">
          <Button variant="outline" type="button" onclick={onOpenToken}>编辑令牌</Button>
          <Button variant="ghost" type="button" onclick={onClearToken}>清除</Button>
        </div>
        <SelectField
          id="settings-theme"
          label="主题"
          value={theme}
          options={themeOptions}
          onValueChange={(value) => onThemeChange(value as Theme)}
        />
      </div>
      </CardContent>
    </Card>
  </div>

  <Card>
    <CardHeader>
      <CardTitle>运行时</CardTitle>
    </CardHeader>
    <CardContent>
    <div class="divide-y divide-border text-sm">
      <div class="grid gap-2 py-3 md:grid-cols-[10rem_minmax(0,1fr)]">
        <span class="text-muted-foreground">请求上限</span>
        <span>{formatBytes(serverInfo?.limits.max_request_bytes ?? 0)}</span>
      </div>
      <div class="grid gap-2 py-3 md:grid-cols-[10rem_minmax(0,1fr)]">
        <span class="text-muted-foreground">超时</span>
        <span>{serverInfo?.limits.request_timeout_seconds ?? "-"} 秒</span>
      </div>
    </div>
    </CardContent>
  </Card>
</section>
