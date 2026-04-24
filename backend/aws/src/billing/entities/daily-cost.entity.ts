import { Entity, Column, PrimaryGeneratedColumn, Index, ManyToOne, JoinColumn } from 'typeorm';
import { Credential } from './credential.entity';

@Entity('aws_daily_costs')
@Index(['credential', 'date'], { unique: true })
export class DailyCost {
    @PrimaryGeneratedColumn()
    id: number;

    @ManyToOne(() => Credential, { onDelete: 'CASCADE' })
    @JoinColumn({ name: 'credential_id' })
    credential: Credential;

    @Column({ name: 'credential_id', type: 'varchar', length: 36 })
    credential_id: string;

    @Column({ type: 'varchar', length: 10 })
    date: string;

    @Column({ type: 'decimal', precision: 18, scale: 6, default: 0 })
    amount: number;

    @Column({ type: 'varchar', length: 10, default: 'USD' })
    unit: string;

    @Column({ default: false })
    estimated: boolean;

    @Column({ name: 'grouped_data', type: 'json', nullable: true })
    grouped_data: any;

    @Column({ name: 'updated_at', type: 'timestamp', default: () => 'CURRENT_TIMESTAMP', onUpdate: 'CURRENT_TIMESTAMP' })
    updated_at: Date;
}
