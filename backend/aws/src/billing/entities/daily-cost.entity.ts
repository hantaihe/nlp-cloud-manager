import { Entity, Column, PrimaryGeneratedColumn, Index } from 'typeorm';

@Entity('aws_daily_costs')
@Index(['credentialName', 'date'], { unique: true })
export class DailyCost {
    @PrimaryGeneratedColumn()
    id: number;

    @Column()
    credentialName: string;

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
