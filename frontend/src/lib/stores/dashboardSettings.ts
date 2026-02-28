import { writable } from 'svelte/store';

export const dashboardSettings = writable({
    pollInterval: 30000,
});
