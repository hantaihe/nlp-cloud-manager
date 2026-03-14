import { Controller, Get, Post, Body, Query } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { DashboardLayout } from './dashboard-layout.entity';

@Controller('api')
export class AppController {
  constructor(
    @InjectRepository(DashboardLayout)
    private readonly dashboardLayoutRepository: Repository<DashboardLayout>,
  ) { }

  @Get('sample')
  getSampleData() {
    return {
      status: 'active',
      message: 'Hello from the NestJS Backend!',
      timestamp: new Date().toISOString(),
    };
  }

  @Get('dashboard/layout')
  async getLayout(@Query('userId') userId: string) {
    const layout = await this.dashboardLayoutRepository.findOne({
      where: { userId: userId || 'default' },
    });
    return {
      data: {
        layoutData: layout ? layout.layoutData : null,
      },
    };
  }

  @Post('dashboard/layout')
  async saveLayout(
    @Body() body: { layoutData: string },
    @Query('userId') userId: string,
  ) {
    const uId = userId || 'default';
    let layout = await this.dashboardLayoutRepository.findOne({
      where: { userId: uId },
    });

    if (layout) {
      layout.layoutData = body.layoutData;
    } else {
      layout = this.dashboardLayoutRepository.create({
        userId: uId,
        layoutData: body.layoutData,
      });
    }

    await this.dashboardLayoutRepository.save(layout);
    return { success: true };
  }
}

