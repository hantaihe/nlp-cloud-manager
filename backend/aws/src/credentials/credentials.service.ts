import { Injectable, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Credential } from '../billing/entities/credential.entity';

export class AWSCredentials {
    id: string;
    name: string;
    access_key_id: string;
    secret_access_key: string;
    session_token?: string;
    region: string;
    account_id?: string;
}

@Injectable()
export class CredentialsService {
    private readonly logger = new Logger(CredentialsService.name);

    constructor(
        @InjectRepository(Credential)
        private credentialRepository: Repository<Credential>,
    ) { }

    async saveCredentials(creds: AWSCredentials) {
        let credential = await this.credentialRepository.findOne({ where: { name: creds.name } });
        if (!credential) {
            credential = new Credential();
            credential.name = creds.name;
        }
        if (creds.access_key_id) credential.access_key_id = creds.access_key_id;
        if (creds.secret_access_key) credential.secret_access_key = creds.secret_access_key;
        credential.session_token = creds.session_token;
        if (creds.region) credential.region = creds.region;
        credential.account_id = creds.account_id;
        return this.credentialRepository.save(credential);
    }

    async getStoredCredentials(name?: string): Promise<AWSCredentials | null> {
        const query = name ? { name } : {};
        const credential = await this.credentialRepository.findOne({ where: query });
        if (!credential) return null;
        return {
            id: credential.id,
            name: credential.name,
            access_key_id: credential.access_key_id,
            secret_access_key: credential.secret_access_key,
            session_token: credential.session_token ?? undefined,
            region: credential.region,
            account_id: credential.account_id ?? undefined,
        };
    }

    async listCredentials() {
        return this.credentialRepository.find();
    }

    async deleteCredentials(name: string) {
        return this.credentialRepository.delete({ name });
    }
}
