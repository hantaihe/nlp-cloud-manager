import { Entity, Column, PrimaryColumn } from 'typeorm';

@Entity('dashboard_layouts')
export class DashboardLayout {
    @PrimaryColumn()
    userId: string;

    @Column({ type: 'text' })
    layoutData: string;

    @Column({ type: 'text', nullable: true })
    settingsData: string | null;
}
