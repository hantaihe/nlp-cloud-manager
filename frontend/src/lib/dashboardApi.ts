import { SERVICES, type ServiceConfig } from './services';

export interface CloudStats {
    totalCost: number;
    costTrend: number;
    topServices: { name: string; cost: number; color?: string }[];
    monthlyData: { month: string; cost: number }[];
    dailyData?: { day: string; cost: number }[];
    activeResources: number;
    budgetUsed: number;
    alerts: number;
    recommendations?: { title: string; info: string; impact?: string }[];
    recentAlerts?: { message: string; severity: 'info' | 'warning' | 'error'; date: string }[];
    resourcesSummary?: { name: string; type: string; status: string }[];
    freeTier?: { name: string; usage: number; limit: number; unit?: string }[];
    billingAccounts?: { name: string; status: string }[];
    assets?: { name: string; type: string; status: string }[];
    quotas?: { name: string; limit: number; usage: number; unit?: string }[];
    governance?: { name: string; status: string; description?: string }[];
    monitoring?: { name: string; value: number; timestamp: string }[];
    logging?: { message: string; severity: string; timestamp: string }[];
    forecastedCost?: number;
    currencyCode?: string;
    unit?: string;
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
        dailyData: data.dailyData ?? [],
        activeResources: data.activeResources ?? 0,
        budgetUsed: data.budgetUsed ?? 0,
        alerts: data.alerts ?? 0,
        recommendations: data.recommendations,
        recentAlerts: data.recentAlerts,
        resourcesSummary: data.resourcesSummary,
        freeTier: data.freeTierUsage || data.freeTier,
        billingAccounts: data.billing_accounts || data.billingAccounts,
        assets: data.assets,
        quotas: data.quota_infos || data.quotas,
        governance: data.constraints || data.governance,
        monitoring: data.time_series || data.monitoring,
        logging: data.entries || data.logging,
        forecastedCost: data.forecastedCost,
        currencyCode: data.currencyCode
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

export async function fetchServiceStats(
    serviceId: string,
    start?: string,
    end?: string,
    granularity: 'DAILY' | 'MONTHLY' = 'MONTHLY',
    visibleTypes?: Set<string>
): Promise<CloudStats> {
    const service = SERVICES.find((s) => s.id === serviceId);
    if (!service) {
        return {
            totalCost: 0,
            costTrend: 0,
            topServices: [],
            monthlyData: [],
            activeResources: 0,
            budgetUsed: 0,
            alerts: 0,
            error: 'Service not found'
        };
    }

    try {
        let endpoint = `${service.apiUrl}/dashboard/stats`;
        const params = new URLSearchParams();
        if (start) params.append('start', start);
        if (end) params.append('end', end);
        if (granularity) params.append('granularity', granularity);
        if (params.toString()) {
            endpoint += `?${params.toString()}`;
        }

        const res = await fetch(endpoint);
        if (!res.ok) return handleFetchError(res, service.name);
        const data = await res.json();
        const stats = parseApiResponse(data, service.color);

        if (!stats) {
            return {
                totalCost: 0,
                costTrend: 0,
                topServices: [],
                monthlyData: [],
                activeResources: 0,
                budgetUsed: 0,
                alerts: 0,
                error: `Invalid ${service.name} response`
            };
        }

        if (serviceId === 'gcp') {
            // visibleTypes가 없으면 모두 호출, 있으면 보이는 카드에 해당하는 것만 호출
            const need = (type: string) => !visibleTypes || visibleTypes.has(type);

            const gcpSubApis: { key: string; url: string; needed: boolean }[] = [
                { key: 'quotas',           url: `${service.apiUrl}/quotas`,                 needed: need('gcp-quotas') },
                { key: 'assets',           url: `${service.apiUrl}/assets`,                 needed: need('gcp-assets') },
                { key: 'billing',          url: `${service.apiUrl}/billing/accounts`,       needed: need('gcp-billing-accounts') },
                { key: 'logging',          url: `${service.apiUrl}/logging/entries`,        needed: need('gcp-logging') },
                { key: 'monitoring',       url: `${service.apiUrl}/monitoring/metrics`,     needed: need('gcp-monitoring') },
                { key: 'governance',       url: `${service.apiUrl}/org-policy/constraints`, needed: need('gcp-governance') },
                { key: 'recommendations',  url: `${service.apiUrl}/recommendations`,        needed: need('gcp-recommendations') },
            ];

            const active = gcpSubApis.filter((a) => a.needed);
            if (active.length > 0) {
                try {
                    const results = await Promise.allSettled(
                        active.map((a) => fetch(a.url).then((r) => r.json()))
                    );
                    active.forEach(({ key }, i) => {
                        const result = results[i];
                        if (result.status !== 'fulfilled') return;
                        const val = result.value;
                        if (key === 'quotas')     stats.quotas = val.quota_infos;
                        if (key === 'assets')     stats.assets = val.assets;
                        if (key === 'billing')    stats.billingAccounts = val.billing_accounts;
                        if (key === 'logging')    stats.logging = val.entries;
                        if (key === 'governance') stats.governance = val.constraints;
                        if (key === 'recommendations') {
                            stats.recommendations = (val.recommendations || []).map((r: any) => ({
                                title: r.description,
                                info: r.category,
                                impact: r.impact ? `$${r.impact}` : undefined
                            }));
                        }
                        if (key === 'monitoring') {
                            const firstSeries = val.time_series?.[0];
                            if (firstSeries) {
                                stats.monitoring = firstSeries.points.map((p: any) => ({
                                    value: p.value,
                                    timestamp: p.interval_end
                                }));
                            }
                        }
                    });
                } catch (e) {
                    console.error('GCP sub-API fetch error:', e);
                }
            }
        }

        return stats;
    } catch (e: any) {
        return {
            totalCost: 0,
            costTrend: 0,
            topServices: [],
            monthlyData: [],
            activeResources: 0,
            budgetUsed: 0,
            alerts: 0,
            error: e.message || `${service.name} connection failed`
        };
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
    const dayMap = new Map<string, number>();

    for (const item of items) {
        for (const m of item.monthlyData) {
            monthMap.set(m.month, (monthMap.get(m.month) || 0) + m.cost);
        }
        if (item.dailyData) {
            for (const d of item.dailyData) {
                dayMap.set(d.day, (dayMap.get(d.day) || 0) + d.cost);
            }
        }
    }

    const monthlyData = Array.from(monthMap.entries())
        .map(([month, cost]) => ({ month, cost }));

    const dailyData = Array.from(dayMap.entries())
        .map(([day, cost]) => ({ day, cost }))
        .sort((a, b) => a.day.localeCompare(b.day));

    const activeResources = items.reduce((s, i) => s + i.activeResources, 0);
    const budgetUsed = Math.round(items.reduce((s, i) => s + i.budgetUsed, 0) / items.length);

    const alerts = items.reduce((s, i) => s + i.alerts, 0);

    const sortedRecommendations = items.flatMap(i => i.recommendations || [])
        .sort((a, b) => {
            const getImpactValue = (impact?: string) => {
                if (!impact) return 0;
                const match = impact.match(/\d+/);
                return match ? parseInt(match[0]) : 0;
            };
            return getImpactValue(b.impact) - getImpactValue(a.impact);
        });

    const recentAlerts = items.flatMap(i => i.recentAlerts || []);
    const resourcesSummary = items.flatMap(i => i.resourcesSummary || []);

    const currencyCode = items.every(i => i.currencyCode === items[0].currencyCode) ? items[0].currencyCode : 'USD';

    return {
        totalCost: Math.round(totalCost),
        costTrend: Math.round(costTrend * 10) / 10,
        topServices: topServices.map(s => ({ ...s, cost: Math.round(s.cost) })),
        monthlyData,
        dailyData: dailyData.length > 0 ? dailyData : undefined,
        activeResources,
        budgetUsed,
        alerts,
        currencyCode,
        unit: currencyCode,
        recommendations: sortedRecommendations.slice(0, 10),
        recentAlerts: recentAlerts.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()).slice(0, 5),
        resourcesSummary
    };
}

export function formatCurrency(value: number, currencyCode: string = 'USD'): string {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currencyCode,
        maximumFractionDigits: 0
    }).format(value);
}
