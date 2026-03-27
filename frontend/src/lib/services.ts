export interface ServiceConfig {
    id: string;
    name: string;
    url: string;
    apiUrl: string;
    color: string;
    icon: string;
    category: string;
    dashboardItems: {
        id: string;
        type: string;
        label: string;
        cols: number;
        rows: number;
    }[];
}

const awsApiUrl = import.meta.env.VITE_AWS_API_URL ?? 'http://localhost:3002';
const azureApiUrl = import.meta.env.VITE_AZURE_API_URL ?? 'http://localhost:8001';
const gcpApiUrl = import.meta.env.VITE_GCP_API_URL ?? 'http://localhost:8002';

export const SERVICES: ServiceConfig[] = [
    {
        id: 'aws',
        name: 'AWS',
        url: import.meta.env.VITE_AWS_IFRAME_URL ?? 'http://127.0.0.1:5175',
        apiUrl: `${awsApiUrl}/billing`,
        color: '#ff9900',
        icon: '/icons/aws.svg',
        category: 'aws',
        dashboardItems: [
            { id: 'aws-total-cost', type: 'aws-total-cost', label: 'Total Cost', cols: 1, rows: 1 },
            { id: 'aws-trend', type: 'aws-trend', label: 'Monthly Trend', cols: 2, rows: 1 },
            { id: 'aws-forecast', type: 'aws-forecast', label: 'Spend Forecast', cols: 2, rows: 1 },
            { id: 'aws-budget', type: 'aws-budget', label: 'Budget Usage', cols: 1, rows: 1 },
            { id: 'aws-freetier', type: 'aws-freetier', label: 'Free Tier', cols: 1, rows: 1 },
            { id: 'aws-recommendations', type: 'aws-recommendations', label: 'Recommendations', cols: 2, rows: 1 }
        ]
    },
    {
        id: 'azure',
        name: 'Azure',
        url: import.meta.env.VITE_AZURE_IFRAME_URL ?? 'http://127.0.0.1:5176',
        apiUrl: azureApiUrl,
        color: '#0078d4',
        icon: '/icons/azure.svg',
        category: 'azure',
        dashboardItems: [
            { id: 'azure-total-cost', type: 'azure-total-cost', label: 'Total Cost', cols: 1, rows: 1 },
            { id: 'azure-trend', type: 'azure-trend', label: 'Monthly Trend', cols: 2, rows: 1 },
            { id: 'azure-forecast', type: 'azure-forecast', label: 'Spend Forecast', cols: 2, rows: 1 },
            { id: 'azure-budget', type: 'azure-budget', label: 'Budget Usage', cols: 1, rows: 1 },
            { id: 'azure-freetier', type: 'azure-freetier', label: 'Free Tier', cols: 1, rows: 1 },
            { id: 'azure-recommendations', type: 'azure-recommendations', label: 'Recommendations', cols: 2, rows: 1 }
        ]
    },
    {
        id: 'gcp',
        name: 'GCP',
        url: import.meta.env.VITE_GCP_IFRAME_URL ?? 'http://127.0.0.1:5177',
        apiUrl: gcpApiUrl,
        color: '#4285f4',
        icon: '/icons/gcp.svg',
        category: 'gcp',
        dashboardItems: [
            { id: 'gcp-total-cost', type: 'gcp-total-cost', label: 'Total Cost', cols: 1, rows: 1 },
            { id: 'gcp-trend', type: 'gcp-trend', label: 'Monthly Trend', cols: 2, rows: 1 },
            { id: 'gcp-budget', type: 'gcp-budget', label: 'Budget Usage', cols: 1, rows: 1 },
            { id: 'gcp-billing-accounts', type: 'gcp-billing-accounts', label: 'Billing Accounts', cols: 2, rows: 1 },
            { id: 'gcp-assets', type: 'gcp-assets', label: 'Active Assets', cols: 1, rows: 1 },
            { id: 'gcp-quotas', type: 'gcp-quotas', label: 'Service Quotas', cols: 2, rows: 1 },
            { id: 'gcp-governance', type: 'gcp-governance', label: 'Governance', cols: 2, rows: 1 },
            { id: 'gcp-monitoring', type: 'gcp-monitoring', label: 'Monitoring', cols: 2, rows: 1 },
            { id: 'gcp-logging', type: 'gcp-logging', label: 'Error Logs', cols: 2, rows: 1 },
            { id: 'gcp-recommendations', type: 'gcp-recommendations', label: 'Recommendations', cols: 2, rows: 1 }
        ]
    }
];

export const COMBINED_ITEMS = [
    { id: 'combined-total', type: 'combined-total', category: 'combined', label: 'Total Cloud Spend', cols: 4, rows: 1 },
    { id: 'combined-trend', type: 'combined-trend', category: 'combined', label: 'Cloud Spend Trend', cols: 2, rows: 1 },
    { id: 'combined-compare', type: 'combined-compare', category: 'combined', label: 'Provider Comparison', cols: 2, rows: 1 },
    { id: 'combined-top', type: 'combined-top', category: 'combined', label: 'Top Services (All)', cols: 2, rows: 1 },
    { id: 'combined-recommendations', type: 'combined-recommendations', category: 'combined', label: 'Cloud Recommendations', cols: 2, rows: 1 },
    { id: 'combined-resources', type: 'combined-resources', category: 'combined', label: 'Total Resources', cols: 1, rows: 1 },
    { id: 'combined-alerts', type: 'combined-alerts', category: 'combined', label: 'Active Alerts', cols: 2, rows: 1 }
];
