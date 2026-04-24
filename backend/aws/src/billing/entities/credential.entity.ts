import { Entity, Column, PrimaryGeneratedColumn, UpdateDateColumn } from 'typeorm';

@Entity('aws_credentials')
export class Credential {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @Column({ unique: true })
    name: string;

    @Column({ name: 'access_key_id' })
    access_key_id: string;

    @Column({ name: 'secret_access_key' })
    secret_access_key: string;

    @Column({ name: 'session_token', nullable: true })
    session_token?: string;

    @Column({ default: 'ap-northeast-2' })
    region: string;

    @Column({ name: 'account_id', nullable: true })
    account_id?: string;

    @UpdateDateColumn({ name: 'updated_at' })
    updated_at: Date;
}
