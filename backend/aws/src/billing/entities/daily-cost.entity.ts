import { Entity, Column, PrimaryGeneratedColumn, Index, ManyToOne, JoinColumn } from 'typeorm';
import { Credential } from './credential.entity';

@Entity('aws_daily_costs')
@Index(['credential', 'date'], { unique: true })
export class DailyCost {
    @PrimaryGeneratedColumn()
    id: number;

    @ManyToOne(() => Credential, { onDelete: 'CASCADE' })
    @JoinColumn({ name: 'credentialId' })
    credential: Credential;

    @Column()
    credentialId: string;

    @Column()
    date: string;

    @Column()
    amount: number;

    @Column()
    unit: string;

    @Column({ default: false })
    estimated: boolean;

    @Column({ type: 'json', nullable: true })
    groupedData: any;

    @Column({ type: 'timestamp', default: () => 'CURRENT_TIMESTAMP' })
    updatedAt: Date;
}
