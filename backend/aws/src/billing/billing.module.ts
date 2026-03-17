import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { BillingService } from './billing.service';
import { BillingController } from './billing.controller';
import { Credential } from './entities/credential.entity';
import { DailyCost } from './entities/daily-cost.entity';

@Module({
    imports: [TypeOrmModule.forFeature([Credential, DailyCost])],
    providers: [BillingService],
    controllers: [BillingController],
})
export class BillingModule { }
