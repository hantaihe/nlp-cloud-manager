import { Entity, Column, PrimaryGeneratedColumn, UpdateDateColumn } from 'typeorm';

@Entity('aws_credentials')
export class Credential {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @Column({ unique: true })
    name: string;

    @Column({ name: 'access_key_id' })
    accessKeyId: string;

    @Column({ name: 'secret_access_key' })
    secretAccessKey: string;

    @Column({ name: 'session_token', nullable: true })
    sessionToken?: string;

    @Column({ default: 'ap-northeast-2' })
    region: string;

    @Column({ name: 'account_id', nullable: true })
    accountId?: string;

    @UpdateDateColumn({ name: 'updated_at' })
    updatedAt: Date;
}
