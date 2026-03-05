
export interface DashboardItem {
    id: string;
    type: 'sample' | 'aws' | 'azure';
    label: string;
    visible: boolean;
    cols: number;
    rows: number;
}
