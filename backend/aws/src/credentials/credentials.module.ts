import { Global, Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { CredentialsService } from './credentials.service';
import { CredentialsController } from './credentials.controller';
import { Credential } from '../billing/entities/credential.entity';

@Global()
@Module({
    imports: [TypeOrmModule.forFeature([Credential])],
    providers: [CredentialsService],
    controllers: [CredentialsController],
    exports: [CredentialsService],
})
export class CredentialsModule { }
