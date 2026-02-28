import { Controller, Get, Post, Body, Query } from '@nestjs/common';

@Controller('api')
export class AppController {
  private layout = JSON.stringify([
    { id: 'sample', type: 'sample', label: 'Sample Service', visible: true, cols: 1, rows: 1 }
  ]);

  @Get('sample')
  getSampleData() {
    return {
      status: 'active',
      message: 'Hello from the NestJS Backend!',
      timestamp: new Date().toISOString(),
    };
  }

  @Get('dashboard/layout')
  getLayout(@Query('userId') userId: string) {
    return {
      data: {
        layoutData: this.layout
      }
    };
  }

  @Post('dashboard/layout')
  saveLayout(@Body() body: { layoutData: string }) {
    this.layout = body.layoutData;
    return { success: true };
  }
}
