import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { DashboardLayout } from './dashboard-layout.entity';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
    }),
    TypeOrmModule.forRootAsync({
      imports: [ConfigModule],
      useFactory: (configService: ConfigService) => ({
        type: 'mysql',
        host: configService.get<string>('DATABASE_HOST', 'localhost'),
        port: configService.get<number>('DATABASE_PORT', 3306),
        username: configService.get<string>('DATABASE_USERNAME', 'root'),
        password: configService.get<string>('DATABASE_PASSWORD', 'root'),
        database: configService.get<string>('DATABASE_DATABASE', 'nlp_cloud_manager'),
        entities: [DashboardLayout],
        synchronize: true, // Auto-create tables in development
      }),
      inject: [ConfigService],
    }),
    TypeOrmModule.forFeature([DashboardLayout]),
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule { }

