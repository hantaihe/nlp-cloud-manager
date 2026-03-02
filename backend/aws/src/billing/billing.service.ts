import { Injectable, Logger, BadRequestException } from '@nestjs/common';
import {
    CostExplorerClient,
    GetCostAndUsageCommand,
} from '@aws-sdk/client-cost-explorer';
import { BudgetsClient, DescribeBudgetsCommand } from '@aws-sdk/client-budgets';
import { FreeTierClient, GetFreeTierUsageCommand } from '@aws-sdk/client-freetier';
import {
    CostOptimizationHubClient,
    ListRecommendationsCommand,
} from '@aws-sdk/client-cost-optimization-hub';

import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Credential } from './entities/credential.entity';

export class AWSCredentials {
    name: string;
    accessKeyId: string;
    secretAccessKey: string;
    sessionToken?: string;
    region: string;
    accountId?: string;
}

@Injectable()
export class BillingService {
    private readonly logger = new Logger(BillingService.name);

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

    private async getClients(creds?: AWSCredentials) {
        const targetCreds = creds || await this.getStoredCredentials();
        if (!targetCreds) {
            throw new BadRequestException('AWS credentials이 필요합니다.');
        }

        const config = {
            region: targetCreds.region,
            credentials: {
                accessKeyId: targetCreds.accessKeyId,
                secretAccessKey: targetCreds.secretAccessKey,
                sessionToken: targetCreds.sessionToken,
            },
        };

        return {
            ceClient: new CostExplorerClient(config),
            budgetsClient: new BudgetsClient(config),
            freeTierClient: new FreeTierClient(config),
            cohClient: new CostOptimizationHubClient(config),
            creds: targetCreds,
        };
    }

    async getAdvancedCost(creds: AWSCredentials | undefined, params: {
        start?: string;
        end?: string;
        granularity?: 'DAILY' | 'MONTHLY' | 'HOURLY';
        metrics?: string[];
        groupBy?: { Type: 'DIMENSION' | 'TAG'; Key: string }[];
        filter?: any;
    }) {
        const { ceClient } = await this.getClients(creds);
        const now = new Date();
        const start = params.start || new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0];
        const end = params.end || new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1).toISOString().split('T')[0];

        try {
            const command = new GetCostAndUsageCommand({
                TimePeriod: {
                    Start: start,
                    End: end,
                },
                Granularity: params.granularity || 'MONTHLY',
                Metrics: params.metrics || ['UnblendedCost'],
                GroupBy: params.groupBy,
                Filter: params.filter,
            });

            const response = await ceClient.send(command);
            return response;
        } catch (error) {
            this.logger.error('Error getAdvancedCost:', error);
            throw error;
        }
    }

    async getCurrentMonthCost(creds?: AWSCredentials) {
        const response = await this.getAdvancedCost(creds, {});
        return response.ResultsByTime;
    }

    async getBudgets(creds?: AWSCredentials) {
        const { budgetsClient, creds: targetCreds } = await this.getClients(creds);
        try {
            const command = new DescribeBudgetsCommand({
                AccountId: targetCreds.accountId || process.env.AWS_ACCOUNT_ID,
            });
            const response = await budgetsClient.send(command);
            return response.Budgets;
        } catch (error) {
            this.logger.error('Error getBudgets:', error);
            throw error;
        }
    }

    async getFreeTierUsage(creds?: AWSCredentials) {
        const { freeTierClient } = await this.getClients(creds);
        try {
            const command = new GetFreeTierUsageCommand({});
            const response = await freeTierClient.send(command);
            return response.freeTierUsages;
        } catch (error) {
            this.logger.error('Error getFreeTierUsage:', error);
            throw error;
        }
    }

    async getRecommendations(creds?: AWSCredentials) {
        const { cohClient } = await this.getClients(creds);
        try {
            const command = new ListRecommendationsCommand({});
            const response = await cohClient.send(command);
            return response.items;
        } catch (error) {
            this.logger.error('Error getRecommendations:', error);
            throw error;
        }
    }

    async getBillingSummary(creds?: AWSCredentials) {
        const [cost, budgets, freeTier, recommendations] = await Promise.all([
            this.getCurrentMonthCost(creds),
            this.getBudgets(creds),
            this.getFreeTierUsage(creds),
            this.getRecommendations(creds),
        ]);


        return {
            currentMonthCost: cost,
            budgets: budgets,
            freeTierUsage: freeTier,
            recommendations: recommendations,
            timestamp: new Date().toISOString(),
        };
    }
}
