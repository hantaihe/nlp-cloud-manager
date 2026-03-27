import { Controller, Get, Query, Post, Body, Delete, Param, BadRequestException } from '@nestjs/common';
import { BillingService } from './billing.service';
import { CredentialsService } from '../credentials/credentials.service';

@Controller('billing')
export class BillingController {
    constructor(
        private readonly billingService: BillingService,
        private readonly credentialsService: CredentialsService,
    ) { }

    @Get('cost')
    async getCost(
        @Query('name') name?: string,
        @Query('start') start?: string,
        @Query('end') end?: string,
        @Query('granularity') granularity?: 'DAILY' | 'MONTHLY' | 'HOURLY',
        @Query('metrics') metrics?: string | string[],
        @Query('group_by_dimension') dimensions?: string | string[],
        @Query('group_by_tag') tags?: string | string[],
        @Query('filter') filterJson?: string,
    ) {
        const creds = await this.credentialsService.getStoredCredentials(name);
        if (!creds) throw new BadRequestException('AWS credentials이 필요합니다.');

        const metricsArray = metrics ? (Array.isArray(metrics) ? metrics : [metrics]) : undefined;
        const dimensionsArray = dimensions ? (Array.isArray(dimensions) ? dimensions : [dimensions]) : [];
        const tagsArray = tags ? (Array.isArray(tags) ? tags : [tags]) : [];

        const groupBy = [
            ...dimensionsArray.map(dim => ({ Type: 'DIMENSION' as const, Key: dim })),
            ...tagsArray.map(tag => ({ Type: 'TAG' as const, Key: tag })),
        ];

        let filter;
        if (filterJson) {
            try {
                filter = JSON.parse(filterJson);
            } catch (e) {
                throw new BadRequestException('Invalid JSON');
            }
        }

        return this.billingService.getAdvancedCost(creds, {
            start,
            end,
            granularity,
            metrics: metricsArray,
            groupBy: groupBy.length > 0 ? groupBy : undefined,
            filter,
        });
    }

    @Get('budgets')
    async getBudgets(@Query('name') name?: string) {
        const creds = await this.credentialsService.getStoredCredentials(name);
        return this.billingService.getBudgets(creds ?? undefined);
    }

    @Get('freetier')
    async getFreeTierUsage(@Query('name') name?: string) {
        const creds = await this.credentialsService.getStoredCredentials(name);
        return this.billingService.getFreeTierUsage(creds ?? undefined);
    }

    @Get('recommendations')
    async getRecommendations(@Query('name') name?: string) {
        const creds = await this.credentialsService.getStoredCredentials(name);
        return this.billingService.getRecommendations(creds ?? undefined);
    }

    @Get('summary')
    async getBillingSummary(@Query('name') name?: string) {
        const creds = await this.credentialsService.getStoredCredentials(name);
        return this.billingService.getBillingSummary(creds ?? undefined);
    }

    @Get('dashboard/stats')
    async getDashboardStats(
        @Query('name') name?: string,
        @Query('start') start?: string,
        @Query('end') end?: string,
        @Query('granularity') granularity: 'DAILY' | 'MONTHLY' = 'MONTHLY',
    ) {
        const creds = await this.credentialsService.getStoredCredentials(name);
        return this.billingService.getDashboardStats(creds ?? undefined, start, end, granularity);
    }
}
