import { Controller, Get } from '@nestjs/common';
import { AppService } from './app.service';

@Controller()
export class AppController {
  constructor(private readonly appService: AppService) { }

  @Get()
  getHello(): string {
    return this.appService.getHello();
  }

  @Get('info')
  getInfo() {
    return {
      name: 'Sample Service',
      version: '1.0.0',
      status: 'healthy',
      port: 3001,
      timestamp: new Date().toISOString(),
    };
  }
}
