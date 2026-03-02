import { Global, Module } from "@nestjs/common";
import { TypeOrmModule } from "@nestjs/typeorm";
import { TypedConfigModule } from "src/config/typed-config.module";
import { TypedConfigService } from "src/config/typed-config.service";

@Global()
@Module({
    imports: [
        TypeOrmModule.forRootAsync({
            imports: [TypedConfigModule],
            useFactory: (configService: TypedConfigService) => ({
                type: 'mysql',
                host: configService.get('database.host'),
                port: configService.get('database.port'),
                username: configService.get('database.username'),
                password: configService.get('database.password'),
                database: configService.get('database.database'),
                synchronize: true,
                autoLoadEntities: true,
            }),
            inject: [TypedConfigService],
        })
    ],
    exports: [TypeOrmModule],
})
export class DatabaseModule { }