<script lang="ts">
  import LegacyApp from "./LegacyApp.svelte";
  import AudioWorkspace from "./lib/studio/AudioWorkspace.svelte";
</script>

{#if import.meta.env.VITE_STUDIO_PREVIEW === "true"}
  <AudioWorkspace />
{:else}
  <LegacyApp />
{/if}
