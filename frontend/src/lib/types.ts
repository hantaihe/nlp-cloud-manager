
export interface DashboardItem {
    id: string;
    type: string;
    category: 'aws' | 'azure' | 'gcp' | 'combined';
    label: string;
    visible: boolean;
    cols: number;
    rows: number;
}
