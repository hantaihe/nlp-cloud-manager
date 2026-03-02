
export interface DashboardItem {
    id: string;
    type: 'sample' | 'aws';
    label: string;
    visible: boolean;
    cols: number;
    rows: number;
}
