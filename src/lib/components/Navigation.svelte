<script lang="ts">
  import { Activity, FileAudio, Library, Settings, SlidersHorizontal, Workflow } from "@lucide/svelte";
  import { Button } from "$lib/components/ui/button/index.js";
  import type { View } from "../types";

  export let activeView: View;
  export let onSelect: (view: View) => void;

  const navItems = [
    { id: "workbench" as View, label: "分离工作台", icon: Workflow },
    { id: "dashboard" as View, label: "状态", icon: Activity },
    { id: "catalog" as View, label: "模型目录", icon: Library },
    { id: "loaded" as View, label: "已加载", icon: SlidersHorizontal },
    { id: "separate" as View, label: "分离音频", icon: FileAudio },
    { id: "settings" as View, label: "设置", icon: Settings },
  ];
</script>

<nav class="hidden border-r border-slate-800 bg-[#081727] px-3 py-6 text-slate-200 lg:block">
  <div class="sticky top-20 flex flex-col gap-1">
    {#each navItems as item}
      <Button
        variant={activeView === item.id ? "secondary" : "ghost"}
        size="sm"
        class={`justify-start ${activeView === item.id ? "bg-[#163252] text-white hover:bg-[#1d4268]" : "text-slate-300 hover:bg-slate-800 hover:text-white"}`}
        type="button"
        onclick={() => onSelect(item.id)}
      >
        <svelte:component this={item.icon} class="size-4" />
        {item.label}
      </Button>
    {/each}
  </div>
</nav>

<div class="border-b border-slate-800 bg-[#081727] p-2 text-slate-200 lg:hidden">
  <div class="grid grid-cols-6 gap-1">
    {#each navItems as item}
      <Button
        variant={activeView === item.id ? "secondary" : "ghost"}
        size="icon-sm"
        type="button"
        onclick={() => onSelect(item.id)}
        aria-label={item.label}
        class={activeView === item.id ? "bg-[#163252] text-white" : "text-slate-300 hover:bg-slate-800 hover:text-white"}
      >
        <svelte:component this={item.icon} class="size-4" />
      </Button>
    {/each}
  </div>
</div>
