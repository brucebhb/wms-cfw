#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF标签生成器 - Linux兼容
使用reportlab生成标签PDF，支持跨平台打印
"""

import os
import tempfile
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import mm, inch
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import black, white
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab未安装，PDF生成功能不可用")

class PDFLabelGenerator:
    """PDF标签生成器"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.font_loaded = False
        
    def _load_fonts(self):
        """加载中文字体"""
        if self.font_loaded or not REPORTLAB_AVAILABLE:
            return
            
        try:
            # 尝试加载系统中文字体
            font_paths = [
                # Linux字体路径
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
                '/usr/share/fonts/truetype/arphic/uming.ttc',
                # Windows字体路径
                'C:/Windows/Fonts/simhei.ttf',
                'C:/Windows/Fonts/simsun.ttc',
                'C:/Windows/Fonts/msyh.ttc',
                # macOS字体路径
                '/System/Library/Fonts/PingFang.ttc',
                '/System/Library/Fonts/STHeiti Light.ttc',
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                        self.font_loaded = True
                        logger.info(f"成功加载字体: {font_path}")
                        break
                    except Exception as e:
                        logger.debug(f"加载字体失败 {font_path}: {e}")
                        continue
            
            if not self.font_loaded:
                logger.warning("未找到中文字体，将使用默认字体")
                
        except Exception as e:
            logger.error(f"字体加载过程出错: {e}")
    
    def generate_label_pdf(self, 
                          labels_data: List[Dict], 
                          output_path: str = None,
                          label_size: Tuple[float, float] = (60*mm, 40*mm),
                          font_size: int = 12,
                          copies: int = 1) -> str:
        """
        生成标签PDF
        
        Args:
            labels_data: 标签数据列表
            output_path: 输出文件路径
            label_size: 标签尺寸 (宽, 高)
            font_size: 字体大小
            copies: 打印份数
            
        Returns:
            生成的PDF文件路径
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab未安装，无法生成PDF")
        
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = os.path.join(self.temp_dir, f'labels_{timestamp}.pdf')
        
        self._load_fonts()
        
        try:
            # 创建PDF文档
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=10*mm,
                leftMargin=10*mm,
                topMargin=10*mm,
                bottomMargin=10*mm
            )
            
            # 构建内容
            story = []
            
            for copy_num in range(copies):
                if copy_num > 0:
                    story.append(Spacer(1, 20))
                
                for i, label_data in enumerate(labels_data):
                    if i > 0:
                        story.append(Spacer(1, 10))
                    
                    # 创建标签表格
                    label_table = self._create_label_table(label_data, font_size)
                    story.append(label_table)
            
            # 生成PDF
            doc.build(story)
            
            logger.info(f"PDF标签生成成功: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"生成PDF标签失败: {e}")
            raise
    
    def _create_label_table(self, label_data: Dict, font_size: int):
        """创建单个标签表格"""
        # 标签内容
        data = [
            ['客户名称:', label_data.get('customer_name', '')],
            ['识别编码:', label_data.get('identification_code', '')],
            ['车牌号码:', label_data.get('plate_number', '')],
            ['件数/板数:', f"{label_data.get('package_count', 0)}件 / {label_data.get('pallet_count', 0)}板"],
            ['重量/体积:', f"{label_data.get('weight', 0)}kg / {label_data.get('volume', 0)}m³"],
            ['打印时间:', datetime.now().strftime('%Y-%m-%d %H:%M')]
        ]
        
        # 创建表格
        table = Table(data, colWidths=[25*mm, 35*mm])
        
        # 设置表格样式
        table.setStyle(TableStyle([
            # 边框
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOX', (0, 0), (-1, -1), 2, colors.black),
            
            # 字体
            ('FONTNAME', (0, 0), (-1, -1), 'ChineseFont' if self.font_loaded else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), font_size),
            
            # 对齐
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),  # 左列右对齐
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),   # 右列左对齐
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # 背景色
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            
            # 内边距
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        
        return table
    
    def generate_simple_label(self, 
                            customer_name: str,
                            identification_code: str,
                            plate_number: str = '',
                            package_count: int = 0,
                            pallet_count: int = 0,
                            weight: float = 0,
                            volume: float = 0,
                            output_path: str = None) -> str:
        """生成单个简单标签"""
        
        label_data = {
            'customer_name': customer_name,
            'identification_code': identification_code,
            'plate_number': plate_number,
            'package_count': package_count,
            'pallet_count': pallet_count,
            'weight': weight,
            'volume': volume
        }
        
        return self.generate_label_pdf([label_data], output_path)
    
    def generate_batch_labels(self, 
                            records: List[Dict],
                            output_path: str = None,
                            copies: int = 1) -> str:
        """批量生成标签"""
        
        labels_data = []
        for record in records:
            label_data = {
                'customer_name': record.get('customer_name', ''),
                'identification_code': record.get('identification_code', ''),
                'plate_number': record.get('plate_number', ''),
                'package_count': record.get('package_count', 0),
                'pallet_count': record.get('pallet_count', 0),
                'weight': record.get('weight', 0),
                'volume': record.get('volume', 0)
            }
            labels_data.append(label_data)
        
        return self.generate_label_pdf(labels_data, output_path, copies=copies)

# 全局实例
pdf_generator = PDFLabelGenerator()

def generate_label_pdf(labels_data: List[Dict], **kwargs) -> str:
    """生成标签PDF的便捷函数"""
    return pdf_generator.generate_label_pdf(labels_data, **kwargs)

def generate_simple_label(customer_name: str, identification_code: str, **kwargs) -> str:
    """生成简单标签的便捷函数"""
    return pdf_generator.generate_simple_label(customer_name, identification_code, **kwargs)

def is_pdf_generation_available() -> bool:
    """检查PDF生成功能是否可用"""
    return REPORTLAB_AVAILABLE
