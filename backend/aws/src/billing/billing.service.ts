import { Injectable, Logger, BadRequestException } from '@nestjs/common';
import {
    CostExplorerClient,
    GetCostAndUsageCommand,
    GetCostForecastCommand,
} from '@aws-sdk/client-cost-explorer';
import { BudgetsClient, DescribeBudgetsCommand } from '@aws-sdk/client-budgets';
import { FreeTierClient, GetFreeTierUsageCommand } from '@aws-sdk/client-freetier';
import {
    CostOptimizationHubClient,
    ListRecommendationsCommand,
} from '@aws-sdk/client-cost-optimization-hub';

import { InjectRepository } from '@nestjs/typeorm';
import { Repository, Between, In } from 'typeorm';
import { Credential } from './entities/credential.entity';
import { DailyCost } from './entities/daily-cost.entity';
import { CredentialsService, AWSCredentials } from '../credentials/credentials.service';

@Injectable()
export class BillingService {
    private readonly logger = new Logger(BillingService.name);

    private statsCache = new Map<string, { at: number; value: any }>();
    private readonly STATS_TTL_MS = 5 * 1000;

    constructor(
        @InjectRepository(DailyCost)
        private dailyCostRepository: Repository<DailyCost>,
        private credentialsService: CredentialsService,
    ) { }

    private async getClients(creds?: AWSCredentials) {
        const targetCreds = creds || await this.credentialsService.getStoredCredentials();
        if (!targetCreds) {
            throw new BadRequestException('Credentials not found');
        }

        const config = {
            region: targetCreds.region,
            credentials: {
                accessKeyId: targetCreds.access_key_id,
                secretAccessKey: targetCreds.secret_access_key,
                sessionToken: targetCreds.session_token,
            },
        };

        const ceClient = new CostExplorerClient(config);
        const budgetsClient = new BudgetsClient(config);
        const freeTierClient = new FreeTierClient(config);
        const cohClient = new CostOptimizationHubClient({
            ...config,
            region: 'us-east-1',
        });

        this.addLoggingMiddleware(ceClient, 'CostExplorer');
        this.addLoggingMiddleware(budgetsClient, 'Budgets');
        this.addLoggingMiddleware(freeTierClient, 'FreeTier');
        this.addLoggingMiddleware(cohClient, 'CostOptimizationHub');

        return {
            ceClient,
            budgetsClient,
            freeTierClient,
            cohClient,
            creds: targetCreds,
        };
    }

    private addLoggingMiddleware(client: any, serviceName: string) {
        client.middlewareStack.add(
            (next: any, context: any) => async (args: any) => {
                const now = Date.now();
                this.logger.log(`SDK Request: AWS ${serviceName}.${context.commandName}`);

                try {
                    const result = await next(args);
                    const duration = Date.now() - now;
                    this.logger.log(`SDK Response: AWS ${serviceName}.${context.commandName} - Success (${duration}ms)`);
                    return result;
                } catch (error) {
                    const duration = Date.now() - now;
                    this.logger.error(`SDK Response: AWS ${serviceName}.${context.commandName} - Error (${duration}ms): ${error.message}`);
                    throw error;
                }
            },
            {
                step: 'build',
                name: 'loggingMiddleware',
            }
        );
    }

    async getAdvancedCost(creds: AWSCredentials | undefined, params: {
        start?: string;
        end?: string;
        granularity?: 'DAILY' | 'MONTHLY' | 'HOURLY';
        metrics?: string[];
        groupBy?: { Type: 'DIMENSION' | 'TAG'; Key: string }[];
        filter?: any;
    }) {
        const targetCreds = creds || await this.credentialsService.getStoredCredentials();
        if (!targetCreds) {
            throw new BadRequestException('Credentials not found');
        }

        const now = new Date();
        const start = params.start || this.formatDate(new Date(now.getFullYear(), now.getMonth(), 1));
        const end = params.end || this.formatDate(new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1));

        const groupByStr = params.groupBy
            ? params.groupBy
                .map((g) => `${g.Type}:${g.Key}`)
                .sort()
                .join(',')
            : null;

        if ((params.granularity === 'DAILY' || !params.granularity) && !params.filter) {
            const cachedData = await this.dailyCostRepository.find({
                where: {
                    credential_id: targetCreds.id,
                    date: Between(start, end),
                },
                order: { date: 'ASC' },
            });

            const startDateObj = new Date(start);
            const endDateObj = new Date(end);
            const diffDays = Math.ceil((endDateObj.getTime() - startDateObj.getTime()) / (1000 * 60 * 60 * 24));

            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);
            const yesterdayStr = this.formatDate(yesterday);

            const hasAllData = cachedData.length >= diffDays;
            const hasGroupingData = !groupByStr || cachedData.every(d => d.grouped_data && d.grouped_data[groupByStr]);
            const hasRecentEstimated = cachedData.some(d => d.estimated && d.date >= yesterdayStr);

            if (hasAllData && hasGroupingData && !hasRecentEstimated) {
                this.logger.log(`${groupByStr ? 'grouped ' : ''} 캐싱 [${targetCreds.id}] ${targetCreds.name}`);
                return {
                    ResultsByTime: cachedData.map(d => ({
                        TimePeriod: { Start: d.date, End: this.getNextDay(d.date) },
                        Total: { UnblendedCost: { Amount: d.amount.toString(), Unit: d.unit } },
                        Groups: groupByStr ? d.grouped_data[groupByStr] : [],
                        Estimated: d.estimated,
                    })),
                };
            }
        }

        const { ceClient } = await this.getClients(targetCreds);

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

            if ((params.granularity === 'DAILY' || !params.granularity) && !params.filter && response.ResultsByTime) {
                await this.saveDailyCostsToDb(targetCreds.id, response.ResultsByTime, params.groupBy);
            }

            return response;
        } catch (error) {
            this.logger.error('Error getAdvancedCost:', error);
            throw error;
        }
    }
    private getNextDay(dateStr: string): string {
        const date = new Date(dateStr);
        date.setDate(date.getDate() + 1);
        return this.formatDate(date);
    }

    private async saveDailyCostsToDb(credential_id: string, results: any[], groupBy?: { Type: string; Key: string }[]) {
        const groupByStr = groupBy
            ? groupBy
                .map((g) => `${g.Type}:${g.Key}`)
                .sort()
                .join(',')
            : null;

        for (const result of results) {
            const date = result.TimePeriod.Start;
            const amount = parseFloat(result.Total?.UnblendedCost?.Amount || '0');
            const unit = result.Total?.UnblendedCost?.Unit || 'USD';
            const estimated = result.Estimated || false;
            const groups = result.Groups || [];

            let dailyCost = await this.dailyCostRepository.findOne({
                where: { credential_id, date },
            });

            if (!dailyCost) {
                dailyCost = new DailyCost();
                dailyCost.credential_id = credential_id;
                dailyCost.date = date;
                dailyCost.grouped_data = {};
            }

            dailyCost.amount = amount;
            dailyCost.unit = unit;
            dailyCost.estimated = estimated;
            dailyCost.updated_at = new Date();

            if (groupByStr) {
                if (!dailyCost.grouped_data) dailyCost.grouped_data = {};
                dailyCost.grouped_data[groupByStr] = groups;
            }

            await this.dailyCostRepository.save(dailyCost);
        }
    }

    private formatDate(date: Date): string {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    async getCurrentMonthCost(creds?: AWSCredentials, start?: string, end?: string) {
        const response = await this.getAdvancedCost(creds, { start, end });
        return response.ResultsByTime;
    }

    async getBudgets(creds?: AWSCredentials) {
        const { budgetsClient, creds: targetCreds } = await this.getClients(creds);
        try {
            const command = new DescribeBudgetsCommand({
                AccountId: targetCreds.account_id || process.env.AWS_ACCOUNT_ID,
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

    async getBillingSummary(creds?: AWSCredentials, start?: string, end?: string) {
        const [cost, budgets, freeTier, recommendations] = await Promise.all([
            this.getCurrentMonthCost(creds, start, end),
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

    async getDashboardStats(creds?: AWSCredentials, start?: string, end?: string, granularity: 'DAILY' | 'MONTHLY' = 'MONTHLY') {
        let ceClient: CostExplorerClient;
        let budgetsClient: BudgetsClient;
        let targetCreds: AWSCredentials;

        try {
            const clients = await this.getClients(creds);
            ceClient = clients.ceClient;
            budgetsClient = clients.budgetsClient;
            targetCreds = clients.creds;
        } catch (error) {
            if (error instanceof BadRequestException && error.message === 'Credentials not found') {
                return {
                    totalCost: 0, costTrend: 0, topServices: [],
                    monthlyData: [], dailyData: [], activeResources: 0,
                    budgetUsed: 0, alerts: 0, error: 'Credentials not found',
                };
            }
            throw error;
        }

        const cacheKey = `${targetCreds.id}|${start ?? ''}|${end ?? ''}|${granularity}`;
        const cached = this.statsCache.get(cacheKey);
        if (cached && Date.now() - cached.at < this.STATS_TTL_MS) return cached.value;

        const now = new Date();
        const currentMonthStart = start || this.formatDate(new Date(now.getFullYear(), now.getMonth(), 1));

        let currentMonthEnd = end;
        if (!currentMonthEnd) {
            currentMonthEnd = this.formatDate(new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1));
        } else {
            const endDate = new Date(currentMonthEnd);
            endDate.setDate(endDate.getDate() + 1);
            currentMonthEnd = this.formatDate(endDate);
        }

        const startDateObj = new Date(currentMonthStart);
        const lastMonthStart = this.formatDate(new Date(startDateObj.getFullYear(), startDateObj.getMonth() - 1, 1));
        const lastMonthEnd = this.formatDate(new Date(startDateObj.getFullYear(), startDateObj.getMonth(), 1));
        const sevenMonthsAgo = this.formatDate(new Date(startDateObj.getFullYear(), startDateObj.getMonth() - 6, 1));


        const advancedCostPromise = this.getAdvancedCost(creds, {
            granularity: 'DAILY',
            start: sevenMonthsAgo,
            end: currentMonthEnd,
            groupBy: [{ Type: 'DIMENSION', Key: 'SERVICE' }],
        }).catch((e) => {
            this.logger.warn(`getAdvancedCost failed in dashboard: ${e?.message || e}`);
            return { ResultsByTime: [] as any[] };
        });

        const [advancedCost, budgets] = await Promise.allSettled([
            advancedCostPromise,
            budgetsClient.send(new DescribeBudgetsCommand({
                AccountId: targetCreds.account_id || process.env.AWS_ACCOUNT_ID,
            })),
        ]);

        const resultsByTime: any[] = advancedCost.status === 'fulfilled'
            ? (advancedCost.value?.ResultsByTime ?? [])
            : [];

        const inRange = (dateStr: string, from: string, to: string) =>
            dateStr >= from && dateStr < to;

        let totalCost = 0;
        let lastTotal = 0;
        const monthlyTotals = new Map<string, number>();
        const dailyTotals = new Map<string, number>();
        const serviceTotals = new Map<string, number>();

        for (const row of resultsByTime) {
            const day = row.TimePeriod?.Start as string | undefined;
            if (!day) continue;
            const rowAmount = parseFloat(row.Total?.UnblendedCost?.Amount || '0');

            dailyTotals.set(day, (dailyTotals.get(day) || 0) + rowAmount);
            const monthKey = day.slice(0, 7);
            monthlyTotals.set(monthKey, (monthlyTotals.get(monthKey) || 0) + rowAmount);

            if (inRange(day, currentMonthStart, currentMonthEnd)) {
                totalCost += rowAmount;
                for (const g of (row.Groups || [])) {
                    const name = g.Keys?.[0] || 'Unknown';
                    const amt = parseFloat(g.Metrics?.UnblendedCost?.Amount || '0');
                    serviceTotals.set(name, (serviceTotals.get(name) || 0) + amt);
                }
            }
            if (inRange(day, lastMonthStart, lastMonthEnd)) {
                lastTotal += rowAmount;
            }
        }

        const costTrend = lastTotal > 0
            ? Math.round(((totalCost - lastTotal) / lastTotal) * 1000) / 10
            : 0;

        const months = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월'];
        const monthlyData: { month: string; cost: number }[] = [];
        const dailyData: { day: string; cost: number }[] = [];
        if (granularity === 'DAILY') {
            for (const [day, cost] of [...dailyTotals.entries()].sort()) {
                const d = new Date(day);
                dailyData.push({ day: `${d.getMonth() + 1}/${d.getDate()}`, cost: Math.round(cost) });
            }
        } else {
            for (const [monthKey, cost] of [...monthlyTotals.entries()].sort()) {
                const monthIdx = parseInt(monthKey.slice(5, 7), 10) - 1;
                monthlyData.push({ month: months[monthIdx], cost: Math.round(cost) });
            }
        }

        const topServices = [...serviceTotals.entries()]
            .map(([name, cost]) => ({ name, cost: Math.round(cost) }))
            .filter((s) => s.cost > 0)
            .sort((a, b) => b.cost - a.cost)
            .slice(0, 5);

        let budgetUsed = 0;
        let alertsCount = 0;
        const recentAlerts: { message: string; severity: 'info' | 'warning' | 'error'; date: string }[] = [];

        if (budgets.status === 'fulfilled' && budgets.value.Budgets?.length) {
            const budget = budgets.value.Budgets[0];
            const limit = parseFloat(budget.BudgetLimit?.Amount || '0');
            const actual = parseFloat(budget.CalculatedSpend?.ActualSpend?.Amount || '0');
            if (limit > 0) {
                budgetUsed = Math.round((actual / limit) * 100);
            }
            for (const b of budgets.value.Budgets) {
                const bLimit = parseFloat(b.BudgetLimit?.Amount || '0');
                const bActual = parseFloat(b.CalculatedSpend?.ActualSpend?.Amount || '0');
                if (bLimit > 0 && bActual > bLimit * 0.8) {
                    alertsCount++;
                    recentAlerts.push({
                        message: `예산 초과: ${b.BudgetName} 예산의 ${Math.round((bActual / bLimit) * 100)}% 사용`,
                        severity: bActual > bLimit ? 'error' : 'warning',
                        date: this.formatDate(new Date())
                    });
                }
            }
        }

        const recommendationsList: { title: string; info: string; impact?: string }[] = [];
        const recommendationsData = await this.getRecommendations(creds);
        if (recommendationsData) {
            (recommendationsData as any[]).slice(0, 5).forEach(rec => {
                recommendationsList.push({
                    title: rec.actionType || '리소스 최적화',
                    info: rec.recommendationLookbackPeriodInDays ? `${rec.recommendationLookbackPeriodInDays}일간의 비용 분석 결과` : '비용 최적화 가능성 감지',
                    impact: rec.estimatedMonthlySavings ? `${rec.estimatedMonthlySavings} 절감 가능` : undefined
                });
            });
        }

        const resourcesSummary = topServices.map(s => ({
            name: s.name,
            type: 'Service',
            status: 'Active'
        }));

        let forecastedCost = 0;
        try {
            const today = new Date();
            const thisMonthStart = this.formatDate(new Date(today.getFullYear(), today.getMonth(), 1));
            const tomorrow = this.formatDate(new Date(today.getFullYear(), today.getMonth(), today.getDate() + 1));
            const nextMonthFirst = this.formatDate(new Date(today.getFullYear(), today.getMonth() + 1, 1));

            let actualThisMonth = 0;
            for (const [day, cost] of dailyTotals) {
                if (day >= thisMonthStart && day < tomorrow) actualThisMonth += cost;
            }

            let remainingForecast = 0;
            if (tomorrow < nextMonthFirst) {
                const forecastResult = await ceClient.send(new GetCostForecastCommand({
                    TimePeriod: { Start: tomorrow, End: nextMonthFirst },
                    Metric: 'UNBLENDED_COST',
                    Granularity: 'MONTHLY',
                }));
                remainingForecast = parseFloat(forecastResult.Total?.Amount || '0');
            }

            forecastedCost = Math.round(actualThisMonth + remainingForecast);
        } catch (e) {
            this.logger.warn(`GetCostForecast failed: ${e}`);
        }

        const result = {
            totalCost: Math.round(totalCost),
            forecastedCost,
            costTrend,
            topServices,
            monthlyData,
            dailyData,
            activeResources: topServices.length,
            budgetUsed,
            alerts: alertsCount,
            recentAlerts,
            recommendations: recommendationsList,
            resourcesSummary,
            timestamp: new Date().toISOString(),
        };
        this.statsCache.set(cacheKey, { at: Date.now(), value: result });
        return result;
    }
}
