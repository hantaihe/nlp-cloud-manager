import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { BillingService } from './billing.service';
import { BillingController } from './billing.controller';
import { Credential } from './entities/credential.entity';

@Module({
    imports: [TypeOrmModule.forFeature([Credential])],
    providers: [BillingService],
    controllers: [BillingController],
})
export class BillingModule { }
