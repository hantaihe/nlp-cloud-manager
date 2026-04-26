import { Entity, Column, PrimaryColumn } from 'typeorm';

@Entity('dashboard_layouts')
export class DashboardLayout {
    @PrimaryColumn({ name: 'user_id' })
    userId: string;

    @Column({ name: 'layout_data', type: 'text' })
    layoutData: string;

    @Column({ name: 'settings_data', type: 'text', nullable: true })
    settingsData: string | null;
}
