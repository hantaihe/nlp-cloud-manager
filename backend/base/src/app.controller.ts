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

  private async findOrCreate(userId: string): Promise<DashboardLayout> {
    const existing = await this.dashboardLayoutRepository.findOne({ where: { userId } });
    if (existing) return existing;
    const record = new DashboardLayout();
    record.userId = userId;
    record.layoutData = '';
    record.settingsData = null;
    return record;
  }

  @Get('dashboard/layout')
  async getLayout(@Query('userId') userId: string) {
    const uId = userId || 'default';
    const layout = await this.dashboardLayoutRepository.findOne({ where: { userId: uId } });
    return {
      data: {
        layoutData: layout?.layoutData ?? null,
        settingsData: layout?.settingsData ?? null,
      },
    };
  }

  @Post('dashboard/layout')
  async saveLayout(
    @Body() body: { layoutData: string },
    @Query('userId') userId: string,
  ) {
    const uId = userId || 'default';
    const record = await this.findOrCreate(uId);
    record.layoutData = body.layoutData;
    await this.dashboardLayoutRepository.save(record);
    return { success: true };
  }

  @Post('dashboard/settings')
  async saveSettings(
    @Body() body: { settingsData: string },
    @Query('userId') userId: string,
  ) {
    const uId = userId || 'default';
    const record = await this.findOrCreate(uId);
    record.settingsData = body.settingsData;
    await this.dashboardLayoutRepository.save(record);
    return { success: true };
  }
}

