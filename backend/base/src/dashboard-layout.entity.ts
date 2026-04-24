import { Entity, Column, PrimaryColumn } from 'typeorm';

@Entity('dashboard_layouts')
export class DashboardLayout {
    @PrimaryColumn({ name: 'user_id' })
    user_id: string;

    @Column({ name: 'layout_data', type: 'text' })
    layout_data: string;

    @Column({ name: 'settings_data', type: 'text', nullable: true })
    settings_data: string | null;
}
