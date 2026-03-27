import { writable } from 'svelte/store';

const now = new Date();
const pad = (n: number) => String(n).padStart(2, '0');
const formatLocal = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const firstDay = formatLocal(new Date(now.getFullYear(), now.getMonth(), 1));
const today = formatLocal(now);

export const dashboardSettings = writable({
    pollInterval: 30000,
    startDate: firstDay,
    endDate: today,
    granularity: 'MONTHLY' as 'MONTHLY' | 'DAILY'
});
