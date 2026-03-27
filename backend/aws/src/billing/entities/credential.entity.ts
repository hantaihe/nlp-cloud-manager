import { Entity, Column, PrimaryGeneratedColumn, UpdateDateColumn } from 'typeorm';

@Entity('aws_credentials')
export class Credential {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @Column({ unique: true })
    name: string;

    @Column()
    accessKeyId: string;

    @Column()
    secretAccessKey: string;

    @Column({ nullable: true })
    sessionToken?: string;

    @Column({ default: 'ap-northeast-2' })
    region: string;

    @Column({ nullable: true })
    accountId?: string;

    @UpdateDateColumn()
    updatedAt: Date;
}
