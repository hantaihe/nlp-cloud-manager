import { Injectable, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Credential } from '../billing/entities/credential.entity';

export class AWSCredentials {
    id: string;
    name: string;
    accessKeyId: string;
    secretAccessKey: string;
    sessionToken?: string;
    region: string;
    accountId?: string;
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
        if (creds.accessKeyId) credential.accessKeyId = creds.accessKeyId;
        if (creds.secretAccessKey) credential.secretAccessKey = creds.secretAccessKey;
        credential.sessionToken = creds.sessionToken;
        if (creds.region) credential.region = creds.region;
        credential.accountId = creds.accountId;
        return this.credentialRepository.save(credential);
    }

    async getStoredCredentials(name?: string): Promise<AWSCredentials | null> {
        const query = name ? { name } : {};
        const credential = await this.credentialRepository.findOne({ where: query });
        if (!credential) return null;
        return {
            id: credential.id,
            name: credential.name,
            accessKeyId: credential.accessKeyId,
            secretAccessKey: credential.secretAccessKey,
            sessionToken: credential.sessionToken ?? undefined,
            region: credential.region,
            accountId: credential.accountId ?? undefined,
        };
    }

    async listCredentials() {
        return this.credentialRepository.find();
    }

    async deleteCredentials(name: string) {
        return this.credentialRepository.delete({ name });
    }
}
