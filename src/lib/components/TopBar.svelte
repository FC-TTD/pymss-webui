<script lang="ts">
  import { KeyRound, Loader2, Moon, RefreshCw, Sun } from "@lucide/svelte";
  import { Badge } from "$lib/components/ui/badge/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import type { HealthResponse } from "../types";

  export let health: HealthResponse | null;
  export let busyAction: string | null;
  export let theme: "light" | "dark";
  export let onRefresh: () => void;
  export let onToggleTheme: () => void;
  export let onOpenToken: () => void;

  $: online = health?.status === "ok";
</script>

<header class="flex min-h-14 items-center border-b border-slate-800 bg-[#081727] px-4 text-white">
  <div class="min-w-0 flex-1">
    <div class="flex items-baseline gap-3">
      <div class="text-[18px] font-medium leading-none tracking-normal">PYMSS Studio</div>
      <span class="hidden text-sm text-slate-300 sm:inline">分离服务</span>
    </div>
  </div>

  <div class="hidden flex-1 justify-center md:flex">
    <Badge variant="outline" class="h-7 gap-2 border-slate-600 bg-slate-900/70 px-3 font-mono font-normal text-slate-100">
      <span class="size-1.5 rounded-full {online ? 'bg-primary' : 'bg-muted-foreground/40'}"></span>
      {online ? "服务正常" : "服务离线"}
    </Badge>
  </div>

  <div class="flex flex-1 justify-end gap-2">
    <Button
      variant="ghost"
      size="icon-sm"
      type="button"
      onclick={onRefresh}
      aria-label="刷新"
      class="text-slate-100 hover:bg-slate-800 hover:text-white"
    >
      {#if busyAction === "refresh"}
        <Loader2 class="size-4 animate-spin" />
      {:else}
        <RefreshCw class="size-4" />
      {/if}
    </Button>
    <Button
      variant="ghost"
      size="icon-sm"
      type="button"
      onclick={onToggleTheme}
      aria-label="切换主题"
      class="text-slate-100 hover:bg-slate-800 hover:text-white"
    >
      {#if theme === "dark"}
        <Sun class="size-4" />
      {:else}
        <Moon class="size-4" />
      {/if}
    </Button>
    <Button variant="outline" size="sm" type="button" onclick={onOpenToken} class="border-slate-600 bg-slate-900/60 text-slate-100 hover:bg-slate-800 hover:text-white">
      <KeyRound class="size-4" />
      <span class="hidden sm:inline">令牌</span>
    </Button>
  </div>
</header>
