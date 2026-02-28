
export interface DashboardItem {
    id: string;
    type: 'sample';
    label: string;
    visible: boolean;
    cols: number; // grid-column-end span
    rows: number; // grid-row-end span
}
