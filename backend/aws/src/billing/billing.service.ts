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
                accessKeyId: targetCreds.accessKeyId,
                secretAccessKey: targetCreds.secretAccessKey,
                sessionToken: targetCreds.sessionToken,
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
                    credentialId: targetCreds.id,
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
            const hasGroupingData = !groupByStr || cachedData.every(d => d.groupedData && d.groupedData[groupByStr]);
            const hasRecentEstimated = cachedData.some(d => d.estimated && d.date >= yesterdayStr);

            if (hasAllData && hasGroupingData && !hasRecentEstimated) {
                this.logger.log(`${groupByStr ? 'grouped ' : ''} 캐싱 [${targetCreds.id}] ${targetCreds.name}`);
                return {
                    ResultsByTime: cachedData.map(d => ({
                        TimePeriod: { Start: d.date, End: this.getNextDay(d.date) },
                        Total: { UnblendedCost: { Amount: d.amount.toString(), Unit: d.unit } },
                        Groups: groupByStr ? d.groupedData[groupByStr] : [],
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

    private async saveDailyCostsToDb(credentialId: string, results: any[], groupBy?: { Type: string; Key: string }[]) {
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
                where: { credentialId, date },
            });

            if (!dailyCost) {
                dailyCost = new DailyCost();
                dailyCost.credentialId = credentialId;
                dailyCost.date = date;
                dailyCost.groupedData = {};
            }

            dailyCost.amount = amount;
            dailyCost.unit = unit;
            dailyCost.estimated = estimated;
            dailyCost.updatedAt = new Date();

            if (groupByStr) {
                if (!dailyCost.groupedData) dailyCost.groupedData = {};
                dailyCost.groupedData[groupByStr] = groups;
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
                    totalCost: 0,
                    costTrend: 0,
                    topServices: [],
                    monthlyData: [],
                    dailyData: [],
                    activeResources: 0,
                    budgetUsed: 0,
                    alerts: 0,
                    error: 'Credentials not found'
                };
            }
            throw error;
        }

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

        const [currentCost, lastCost, monthlyCosts, serviceCosts, budgets] = await Promise.allSettled([
            ceClient.send(new GetCostAndUsageCommand({
                TimePeriod: { Start: currentMonthStart, End: currentMonthEnd },
                Granularity: 'MONTHLY',
                Metrics: ['UnblendedCost'],
            })),
            ceClient.send(new GetCostAndUsageCommand({
                TimePeriod: { Start: lastMonthStart, End: lastMonthEnd },
                Granularity: 'MONTHLY',
                Metrics: ['UnblendedCost'],
            })),
            ceClient.send(new GetCostAndUsageCommand({
                TimePeriod: { Start: sevenMonthsAgo, End: currentMonthEnd },
                Granularity: granularity,
                Metrics: ['UnblendedCost'],
            })),
            ceClient.send(new GetCostAndUsageCommand({
                TimePeriod: { Start: currentMonthStart, End: currentMonthEnd },
                Granularity: 'MONTHLY',
                Metrics: ['UnblendedCost'],
                GroupBy: [{ Type: 'DIMENSION', Key: 'SERVICE' }],
            })),
            budgetsClient.send(new DescribeBudgetsCommand({
                AccountId: targetCreds.accountId || process.env.AWS_ACCOUNT_ID,
            })),
        ]);

        let totalCost = 0;
        if (currentCost.status === 'fulfilled' && currentCost.value.ResultsByTime?.length) {
            totalCost = parseFloat(currentCost.value.ResultsByTime[0].Total?.UnblendedCost?.Amount || '0');
        }

        let costTrend = 0;
        if (lastCost.status === 'fulfilled' && lastCost.value.ResultsByTime?.length) {
            const lastTotal = parseFloat(lastCost.value.ResultsByTime[0].Total?.UnblendedCost?.Amount || '0');
            if (lastTotal > 0) {
                costTrend = Math.round(((totalCost - lastTotal) / lastTotal) * 1000) / 10;
            }
        }

        const months = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월'];
        const monthlyData: { month: string; cost: number }[] = [];
        const dailyData: { day: string; cost: number }[] = [];
        if (monthlyCosts.status === 'fulfilled' && monthlyCosts.value.ResultsByTime) {
            for (const period of monthlyCosts.value.ResultsByTime) {
                const startDate = new Date(period.TimePeriod?.Start || '');
                if (granularity === 'DAILY') {
                    dailyData.push({
                        day: `${startDate.getMonth() + 1}/${startDate.getDate()}`,
                        cost: Math.round(parseFloat(period.Total?.UnblendedCost?.Amount || '0'))
                    });
                } else {
                    monthlyData.push({
                        month: months[startDate.getMonth()],
                        cost: Math.round(parseFloat(period.Total?.UnblendedCost?.Amount || '0'))
                    });
                }
            }
        }

        const topServices: { name: string; cost: number }[] = [];
        if (serviceCosts.status === 'fulfilled' && serviceCosts.value.ResultsByTime?.length) {
            const groups = serviceCosts.value.ResultsByTime[0].Groups || [];
            const sorted = groups
                .map((g) => ({
                    name: g.Keys?.[0] || 'Unknown',
                    cost: Math.round(parseFloat(g.Metrics?.UnblendedCost?.Amount || '0')),
                }))
                .filter((s) => s.cost > 0)
                .sort((a, b) => b.cost - a.cost);
            topServices.push(...sorted.slice(0, 5));
        }

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
            const actualResult = await ceClient.send(new GetCostAndUsageCommand({
                TimePeriod: { Start: thisMonthStart, End: tomorrow },
                Granularity: 'MONTHLY',
                Metrics: ['UnblendedCost'],
            }));
            if (actualResult.ResultsByTime?.length) {
                actualThisMonth = parseFloat(actualResult.ResultsByTime[0].Total?.UnblendedCost?.Amount || '0');
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

        return {
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
    }
}
