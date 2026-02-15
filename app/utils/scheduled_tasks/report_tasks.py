# -*- coding: utf-8 -*-
"""
定时任务 - 工时报表自动生成
包含：每月自动生成报表、报表归档、报表发送
"""
import logging
import os
from datetime import datetime

from app.models.base import get_db_session
from app.models.report import GeneratedByEnum, ArchiveStatusEnum
from app.models import OutputFormatEnum
from app.services.report_service import ReportService
from app.services.report_excel_service import ReportExcelService

logger = logging.getLogger(__name__)


def monthly_report_generation_task():
    """
    每月自动生成工时报表任务
    
    执行时间：每月1号 09:00
    功能：
    1. 获取所有启用的月度报表模板
    2. 生成上月报表
    3. 导出为文件
    4. 归档
    5. 发送（TODO）
    """
    try:
        with get_db_session() as db:
            # 获取上月周期
            period = ReportService.get_last_month_period()
            year, month = map(int, period.split('-'))
            
            logger.info(f"[{datetime.now()}] 开始生成 {period} 月度报表...")
            
            # 获取启用的月度报表模板
            templates = ReportService.get_active_monthly_templates(db)
            
            if not templates:
                logger.info(f"[{datetime.now()}] 无启用的月度报表模板")
                return {
                    'success': True,
                    'message': '无启用的月度报表模板',
                    'template_count': 0,
                    'success_count': 0,
                    'failed_count': 0,
                }
            
            logger.info(f"[{datetime.now()}] 找到 {len(templates)} 个启用的报表模板")
            
            success_count = 0
            failed_count = 0
            results = []
            
            for template in templates:
                try:
                    logger.info(f"[{datetime.now()}] 正在生成报表: {template.name} - {period}")
                    
                    # 生成报表数据
                    data = ReportService.generate_report(
                        db=db,
                        template_id=template.id,
                        period=period,
                        generated_by=GeneratedByEnum.SYSTEM.value
                    )
                    
                    # 导出为文件
                    if template.output_format == OutputFormatEnum.EXCEL.value:
                        file_path = ReportExcelService.export_to_excel(
                            data=data,
                            template_name=template.name
                        )
                        file_size = os.path.getsize(file_path)
                        row_count = len(data['summary'])
                    else:
                        logger.warning(f"暂不支持的输出格式: {template.output_format}")
                        continue
                    
                    # 归档
                    archive = ReportService.archive_report(
                        db=db,
                        template_id=template.id,
                        period=period,
                        file_path=file_path,
                        file_size=file_size,
                        row_count=row_count,
                        generated_by=GeneratedByEnum.SYSTEM.value,
                        status=ArchiveStatusEnum.SUCCESS.value
                    )
                    
                    # TODO: 发送报表给收件人
                    # send_report_to_recipients(db, archive)
                    
                    success_count += 1
                    results.append({
                        'template_name': template.name,
                        'status': 'success',
                        'archive_id': archive.id,
                        'file_path': file_path,
                        'row_count': row_count,
                    })
                    
                    logger.info(
                        f"✅ 报表生成成功: {template.name} - {period} "
                        f"(归档ID: {archive.id}, 行数: {row_count})"
                    )
                    
                except Exception as e:
                    failed_count += 1
                    error_msg = str(e)
                    
                    # 记录失败归档
                    try:
                        ReportService.archive_report(
                            db=db,
                            template_id=template.id,
                            period=period,
                            file_path="",
                            file_size=0,
                            row_count=0,
                            generated_by=GeneratedByEnum.SYSTEM.value,
                            status=ArchiveStatusEnum.FAILED.value,
                            error_message=error_msg
                        )
                    except Exception as archive_error:
                        logger.error(f"记录失败归档时出错: {str(archive_error)}")
                    
                    results.append({
                        'template_name': template.name,
                        'status': 'failed',
                        'error': error_msg,
                    })
                    
                    logger.error(f"❌ 报表生成失败: {template.name} - {period}: {error_msg}")
            
            # 生成总结
            summary = {
                'success': True,
                'period': period,
                'template_count': len(templates),
                'success_count': success_count,
                'failed_count': failed_count,
                'results': results,
                'timestamp': datetime.now().isoformat(),
            }
            
            logger.info(
                f"[{datetime.now()}] 月度报表生成完成: "
                f"总计 {len(templates)} 个模板, "
                f"成功 {success_count} 个, "
                f"失败 {failed_count} 个"
            )
            
            return summary
            
    except Exception as e:
        logger.error(f"[{datetime.now()}] 月度报表生成任务失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
        }


def send_report_to_recipients(db, archive):
    """
    发送报表给收件人
    
    TODO: 实现邮件/企业微信发送功能
    """
    from app.models import ReportRecipient
    
    # 获取收件人列表
    recipients = db.query(ReportRecipient).filter(
        ReportRecipient.template_id == archive.template_id,
        ReportRecipient.enabled == True
    ).all()
    
    if not recipients:
        logger.info(f"报表 {archive.id} 没有配置收件人")
        return
    
    logger.info(f"报表 {archive.id} 有 {len(recipients)} 个收件人")
    
    # TODO: 根据 delivery_method 发送报表
    # - EMAIL: 发送邮件附件
    # - WECHAT: 发送企业微信消息
    # - DOWNLOAD: 发送下载链接
    
    for recipient in recipients:
        try:
            if recipient.delivery_method == 'EMAIL':
                # send_email(recipient.recipient_email, archive)
                logger.info(f"TODO: 发送邮件到 {recipient.recipient_email}")
            elif recipient.delivery_method == 'WECHAT':
                # send_wechat(recipient.recipient_id, archive)
                logger.info(f"TODO: 发送企业微信到用户 {recipient.recipient_id}")
            elif recipient.delivery_method == 'DOWNLOAD':
                # send_download_link(recipient.recipient_id, archive)
                logger.info(f"TODO: 发送下载链接到用户 {recipient.recipient_id}")
        except Exception as e:
            logger.error(f"发送报表给收件人 {recipient.id} 失败: {str(e)}")


def test_report_generation():
    """
    测试报表生成功能
    
    可用于手动测试
    """
    logger.info("开始测试报表生成功能...")
    result = monthly_report_generation_task()
    logger.info(f"测试完成: {result}")
    return result


# 导出任务函数供调度器使用
__all__ = [
    'monthly_report_generation_task',
    'send_report_to_recipients',
    'test_report_generation',
]
