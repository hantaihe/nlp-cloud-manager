export interface EnvironmentVariables {
    database: {
        host: string;
        port: number;
        username: string;
        password: string;
        database: string;
    }
}

export default (): EnvironmentVariables => ({
    database: {
        host: process.env.DATABASE_HOST || 'localhost',
        port: parseInt(process.env.DATABASE_PORT ?? '3306', 10),
        username: process.env.DATABASE_USERNAME || 'root',
        password: process.env.DATABASE_PASSWORD || 'root',
        database: process.env.DATABASE_DATABASE || 'nlp_cloud_manager',
    }
});