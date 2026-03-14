
export interface DashboardItem {
    id: string;
    type: 'sample' | 'aws' | 'azure' | 'gcp';
    label: string;
    visible: boolean;
    cols: number;
    rows: number;
}
