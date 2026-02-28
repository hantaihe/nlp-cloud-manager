export interface DashboardItem {
    id: string;
    type: string;
    label: string;
    visible: boolean;
    cols: number;
    rows: number;
}

const BASE_API_URL = 'http://localhost:3000/api';

export async function fetchDashboardLayout(): Promise<any[]> {
    try {
        const res = await fetch(`${BASE_API_URL}/dashboard/layout?userId=default`);
        if (!res.ok) throw new Error('fetch failed');
        const json = await res.json();
        if (json.data && json.data.layoutData) {
            return JSON.parse(json.data.layoutData);
        }
        return [];
    } catch (err) {
        console.error('대시보드 에러:', err);
        return [];
    }
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
