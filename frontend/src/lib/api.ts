export interface DashboardItem {
    id: string;
    type: string;
    label: string;
    visible: boolean;
    cols: number;
    rows: number;
}

export interface DashboardPersistedSettings {
    pollInterval: number;
    startDate: string;
    endDate: string;
    granularity: 'MONTHLY' | 'DAILY';
    selectedProviders: Record<string, boolean>;
}

const BASE_API_URL = import.meta.env.VITE_BASE_API_URL ?? 'http://localhost:3000/api';
const GCP_API_URL = import.meta.env.VITE_GCP_API_URL ?? 'http://localhost:8002';

export interface GcpCredential {
    id: string;
    name: string;
    project_id: string;
    billing_account_id: string | null;
    updated_at: string;
}

export async function fetchGcpCredentials(): Promise<GcpCredential[]> {
    try {
        const res = await fetch(`${GCP_API_URL}/credentials`);
        if (!res.ok) throw new Error('fetch failed');
        return res.json();
    } catch {
        return [];
    }
}

export async function updateGcpBillingAccount(name: string, billing_account_id: string): Promise<boolean> {
    try {
        const res = await fetch(`${GCP_API_URL}/credentials/${encodeURIComponent(name)}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ billing_account_id })
        });
        return res.ok;
    } catch {
        return false;
    }
}

export async function fetchDashboardData(): Promise<{ layout: any[]; settings: DashboardPersistedSettings | null }> {
    try {
        const res = await fetch(`${BASE_API_URL}/dashboard/layout?userId=default`);
        if (!res.ok) throw new Error('fetch failed');
        const json = await res.json();
        const layout = json.data?.layoutData ? JSON.parse(json.data.layoutData) : [];
        const settings = json.data?.settingsData ? JSON.parse(json.data.settingsData) : null;
        return { layout, settings };
    } catch (err) {
        console.error('대시보드 로드 에러:', err);
        return { layout: [], settings: null };
    }
}

/** @deprecated fetchDashboardData 사용 권장 */
export async function fetchDashboardLayout(): Promise<any[]> {
    const { layout } = await fetchDashboardData();
    return layout;
}

export async function saveDashboardLayout(layout: any[]): Promise<boolean> {
    try {
        const res = await fetch(`${BASE_API_URL}/dashboard/layout?userId=default`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ layoutData: JSON.stringify(layout) })
        });
        return res.ok;
    } catch (err) {
        console.error('대시보드 저장 에러:', err);
        return false;
    }
}

export async function saveDashboardSettings(settings: DashboardPersistedSettings): Promise<boolean> {
    try {
        const res = await fetch(`${BASE_API_URL}/dashboard/settings?userId=default`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ settingsData: JSON.stringify(settings) })
        });
        return res.ok;
    } catch (err) {
        console.error('대시보드 설정 저장 에러:', err);
        return false;
    }
}
