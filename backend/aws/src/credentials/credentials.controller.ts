import { Controller, Get, Query, Post, Body, Delete, Param } from '@nestjs/common';
import { AWSCredentials, CredentialsService } from './credentials.service';

@Controller('credentials')
export class CredentialsController {
    constructor(private readonly credentialsService: CredentialsService) { }

    @Post()
    async saveCredentials(@Body() creds: AWSCredentials) {
        return this.credentialsService.saveCredentials(creds);
    }

    @Get()
    async listCredentials() {
        return this.credentialsService.listCredentials();
    }

    @Delete(':name')
    async deleteCredentials(@Param('name') name: string) {
        return this.credentialsService.deleteCredentials(name);
    }

    @Get('status')
    async getCredentialStatus(@Query('name') name?: string) {
        const creds = await this.credentialsService.getStoredCredentials(name);
        return {
            isSet: !!creds,
            name: creds?.name,
            region: creds?.region,
            accountId: creds?.accountId,
        };
    }
}
