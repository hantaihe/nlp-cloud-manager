import { Module } from '@nestjs/common';
import { BillingModule } from './billing/billing.module';
import { DatabaseModule } from './database/database.module';
import { TypedConfigModule } from 'src/config/typed-config.module';

@Module({
  imports: [
    TypedConfigModule,
    DatabaseModule,
    BillingModule,
  ],
})
export class AppModule { }
