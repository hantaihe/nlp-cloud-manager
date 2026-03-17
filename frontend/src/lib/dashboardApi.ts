import { SERVICES, type ServiceConfig } from './services';

export interface CloudStats {
    totalCost: number;
    costTrend: number;
    topServices: { name: string; cost: number; color?: string }[];
    monthlyData: { month: string; cost: number }[];
    activeResources: number;
    budgetUsed: number;
    alerts: number;
    recommendations?: { title: string; info: string; impact?: string }[];
    recentAlerts?: { message: string; severity: 'info' | 'warning' | 'error'; date: string }[];
    resourcesSummary?: { name: string; type: string; status: string }[];
    error?: string;
}

function parseApiResponse(data: any, providerColor: string): CloudStats | null {
    if (!data || data.totalCost === undefined) return null;
    return {
        totalCost: data.totalCost ?? 0,
        costTrend: data.costTrend ?? 0,
        topServices: (data.topServices ?? []).map((s: any) => ({
            name: s.name,
            cost: s.cost,
            color: s.color || providerColor
        })),
        monthlyData: data.monthlyData ?? [],
        activeResources: data.activeResources ?? 0,
        budgetUsed: data.budgetUsed ?? 0,
        alerts: data.alerts ?? 0,
        recommendations: data.recommendations,
        recentAlerts: data.recentAlerts,
        resourcesSummary: data.resourcesSummary
    };
}

async function handleFetchError(res: Response, provider: string): Promise<CloudStats> {
    let message = `${provider} API error`;
    try {
        const errorData = await res.json();
        message = errorData.detail || errorData.message || message;
    } catch {
        console.log('parse error');
    }
    return {
        totalCost: 0,
        costTrend: 0,
        topServices: [],
        monthlyData: [],
        activeResources: 0,
        budgetUsed: 0,
        alerts: 0,
        error: message
    };
}

export async function fetchServiceStats(serviceId: string): Promise<CloudStats> {
    const service = SERVICES.find(s => s.id === serviceId);
    if (!service) {
        return { totalCost: 0, costTrend: 0, topServices: [], monthlyData: [], activeResources: 0, budgetUsed: 0, alerts: 0, error: 'Service not found' };
    }

    try {
        const endpoint = service.id === 'aws' ? `${service.apiUrl}/dashboard/stats` : `${service.apiUrl}/dashboard/stats`;
        const res = await fetch(endpoint);
        if (!res.ok) return handleFetchError(res, service.name);
        const data = await res.json();
        return parseApiResponse(data, service.color) || { totalCost: 0, costTrend: 0, topServices: [], monthlyData: [], activeResources: 0, budgetUsed: 0, alerts: 0, error: `Invalid ${service.name} response` };
    } catch (e: any) {
        return { totalCost: 0, costTrend: 0, topServices: [], monthlyData: [], activeResources: 0, budgetUsed: 0, alerts: 0, error: e.message || `${service.name} connection failed` };
    }
}


export const fetchAwsStats = () => fetchServiceStats('aws');
export const fetchAzureStats = () => fetchServiceStats('azure');
export const fetchGcpStats = () => fetchServiceStats('gcp');

export function getCombinedStats(
    providers: Record<string, CloudStats | undefined>,
    selected: Record<string, boolean>
): CloudStats {
    const items: CloudStats[] = [];
    SERVICES.forEach(service => {
        if (selected[service.id] && providers[service.id]) {
            items.push(providers[service.id]!);
        }
    });

    if (items.length === 0) {
        return {
            totalCost: 0,
            costTrend: 0,
            topServices: [],
            monthlyData: [],
            activeResources: 0,
            budgetUsed: 0,
            alerts: 0
        };
    }

    const totalCost = items.reduce((s, i) => s + i.totalCost, 0);
    const costTrend = totalCost === 0 ? 0 :
        items.reduce((s, i) => s + i.costTrend * i.totalCost, 0) / totalCost;
    const allServices = items.flatMap((i) => i.topServices);
    allServices.sort((a, b) => b.cost - a.cost);
    const topServices = allServices.slice(0, 5);

    const monthMap = new Map<string, number>();
    for (const item of items) {
        for (const m of item.monthlyData) {
            monthMap.set(m.month, (monthMap.get(m.month) || 0) + m.cost);
        }
    }
    const monthlyData = Array.from(monthMap.entries())
        .map(([month, cost]) => ({ month, cost }));

    const activeResources = items.reduce((s, i) => s + i.activeResources, 0);
    const budgetUsed = Math.round(items.reduce((s, i) => s + i.budgetUsed, 0) / items.length);
    const alerts = items.reduce((s, i) => s + i.alerts, 0);

    const recommendations = items.flatMap(i => i.recommendations || []);
    const recentAlerts = items.flatMap(i => i.recentAlerts || []);
    const resourcesSummary = items.flatMap(i => i.resourcesSummary || []);

    return {
        totalCost,
        costTrend: Math.round(costTrend * 10) / 10,
        topServices,
        monthlyData,
        activeResources,
        budgetUsed,
        alerts,
        recommendations,
        recentAlerts,
        resourcesSummary
    };
}

export function formatCurrency(value: number): string {
    if (value >= 1_000_000) {
        return `$${(value / 1_000_000).toFixed(1)}M`;
    }
    if (value >= 1_000) {
        return `$${(value / 1_000).toFixed(1)}K`;
    }
    return `$${value.toFixed(0)}`;
}
