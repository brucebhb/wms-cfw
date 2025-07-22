#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
输入验证工具类
增强的用户输入验证和清理机制
"""

import re
import html
import bleach
from datetime import datetime
from flask import request
from app.utils.exception_handler import ValidationException

class InputSanitizer:
    """输入清理工具类"""
    
    # 允许的HTML标签（用于富文本字段）
    ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li']
    ALLOWED_ATTRIBUTES = {}
    
    @staticmethod
    def sanitize_string(value, max_length=None, allow_html=False):
        """清理字符串输入"""
        if not value:
            return ''
        
        # 转换为字符串
        value = str(value).strip()
        
        if not allow_html:
            # 转义HTML字符
            value = html.escape(value)
        else:
            # 清理HTML，只保留安全标签
            value = bleach.clean(
                value, 
                tags=InputSanitizer.ALLOWED_TAGS,
                attributes=InputSanitizer.ALLOWED_ATTRIBUTES,
                strip=True
            )
        
        # 检查长度限制
        if max_length and len(value) > max_length:
            raise ValidationException(f"输入长度不能超过{max_length}个字符")
        
        return value
    
    @staticmethod
    def sanitize_number(value, field_name, min_value=None, max_value=None, decimal_places=None):
        """清理数字输入"""
        if not value and value != 0:
            return 0
        
        try:
            # 移除非数字字符（保留小数点和负号）
            cleaned = re.sub(r'[^\d.-]', '', str(value))
            num_value = float(cleaned)
            
            # 检查范围
            if min_value is not None and num_value < min_value:
                raise ValidationException(f"{field_name}不能小于{min_value}")
            if max_value is not None and num_value > max_value:
                raise ValidationException(f"{field_name}不能大于{max_value}")
            
            # 处理小数位数
            if decimal_places is not None:
                num_value = round(num_value, decimal_places)
            
            return num_value
        except (ValueError, TypeError):
            raise ValidationException(f"{field_name}必须是有效数字")
    
    @staticmethod
    def sanitize_integer(value, field_name, min_value=0, max_value=None):
        """清理整数输入"""
        if not value and value != 0:
            return 0
        
        try:
            # 移除非数字字符
            cleaned = re.sub(r'[^\d-]', '', str(value))
            int_value = int(cleaned)
            
            # 检查范围
            if min_value is not None and int_value < min_value:
                raise ValidationException(f"{field_name}不能小于{min_value}")
            if max_value is not None and int_value > max_value:
                raise ValidationException(f"{field_name}不能大于{max_value}")
            
            return int_value
        except (ValueError, TypeError):
            raise ValidationException(f"{field_name}必须是有效整数")

class FormValidator:
    """表单验证工具类"""
    
    # 车牌号正则表达式
    PLATE_NUMBER_PATTERN = re.compile(r'^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领A-Z]{1}[A-Z]{1}[A-Z0-9]{4}[A-Z0-9挂学警港澳]{1}$')
    
    # 手机号正则表达式
    PHONE_PATTERN = re.compile(r'^1[3-9]\d{9}$')
    
    # 邮箱正则表达式
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    @staticmethod
    def validate_plate_number(plate_number, required=True):
        """验证车牌号"""
        if not plate_number:
            if required:
                raise ValidationException("车牌号不能为空")
            return ''
        
        # 清理输入
        plate_number = InputSanitizer.sanitize_string(plate_number, max_length=10).upper()
        
        # 特殊情况：快递公司
        express_companies = ['顺丰', '跨越', '安能', '德邦', '中通', '圆通', '申通', '韵达']
        if any(company in plate_number for company in express_companies):
            return plate_number
        
        # 验证车牌号格式
        if not FormValidator.PLATE_NUMBER_PATTERN.match(plate_number):
            raise ValidationException(f"车牌号格式错误: {plate_number}")
        
        return plate_number
    
    @staticmethod
    def validate_customer_name(customer_name, required=True):
        """验证客户名称"""
        if not customer_name:
            if required:
                raise ValidationException("客户名称不能为空")
            return ''
        
        customer_name = InputSanitizer.sanitize_string(customer_name, max_length=100)
        
        # 检查是否包含特殊字符
        if re.search(r'[<>"\']', customer_name):
            raise ValidationException("客户名称不能包含特殊字符")
        
        return customer_name
    
    @staticmethod
    def validate_identification_code(code, required=True):
        """验证识别编码"""
        if not code:
            if required:
                raise ValidationException("识别编码不能为空")
            return ''
        
        code = InputSanitizer.sanitize_string(code, max_length=200)
        
        # 检查格式：仓库前缀/客户全称/车牌/日期/序号
        parts = code.split('/')
        if len(parts) < 4:
            raise ValidationException("识别编码格式错误，应为：仓库前缀/客户全称/车牌/日期/序号")
        
        # 验证仓库前缀
        warehouse_prefix = parts[0].upper()
        valid_prefixes = ['PH', 'KS', 'CD', 'PX']
        if warehouse_prefix not in valid_prefixes:
            raise ValidationException(f"无效的仓库前缀: {warehouse_prefix}，有效值: {', '.join(valid_prefixes)}")
        
        return code
    
    @staticmethod
    def validate_datetime(datetime_str, field_name, required=True):
        """验证日期时间"""
        if not datetime_str:
            if required:
                raise ValidationException(f"{field_name}不能为空")
            return None
        
        try:
            # 支持多种日期格式
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M',
                '%Y-%m-%d',
                '%Y/%m/%d %H:%M:%S',
                '%Y/%m/%d %H:%M',
                '%Y/%m/%d'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(datetime_str, fmt)
                except ValueError:
                    continue
            
            raise ValueError("无法解析日期格式")
            
        except ValueError:
            raise ValidationException(f"{field_name}日期格式错误")
    
    @staticmethod
    def validate_phone(phone, required=False):
        """验证手机号"""
        if not phone:
            if required:
                raise ValidationException("手机号不能为空")
            return ''
        
        phone = re.sub(r'[^\d]', '', str(phone))
        
        if not FormValidator.PHONE_PATTERN.match(phone):
            raise ValidationException("手机号格式错误")
        
        return phone
    
    @staticmethod
    def validate_email(email, required=False):
        """验证邮箱"""
        if not email:
            if required:
                raise ValidationException("邮箱不能为空")
            return ''
        
        email = InputSanitizer.sanitize_string(email, max_length=100).lower()
        
        if not FormValidator.EMAIL_PATTERN.match(email):
            raise ValidationException("邮箱格式错误")
        
        return email

class RequestValidator:
    """请求验证工具类"""
    
    @staticmethod
    def validate_json_request():
        """验证JSON请求"""
        if not request.is_json:
            raise ValidationException("请求必须是JSON格式")
        
        data = request.get_json()
        if not data:
            raise ValidationException("请求数据不能为空")
        
        return data
    
    @staticmethod
    def validate_form_request():
        """验证表单请求"""
        if not request.form:
            raise ValidationException("表单数据不能为空")
        
        return request.form
    
    @staticmethod
    def validate_file_upload(file_field, allowed_extensions=None, max_size=None):
        """验证文件上传"""
        if file_field not in request.files:
            raise ValidationException("未找到上传文件")
        
        file = request.files[file_field]
        if file.filename == '':
            raise ValidationException("未选择文件")
        
        # 检查文件扩展名
        if allowed_extensions:
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            if ext not in allowed_extensions:
                raise ValidationException(f"不支持的文件类型，允许的类型: {', '.join(allowed_extensions)}")
        
        # 检查文件大小
        if max_size:
            file.seek(0, 2)  # 移动到文件末尾
            size = file.tell()
            file.seek(0)  # 重置到文件开头
            
            if size > max_size:
                raise ValidationException(f"文件大小不能超过{max_size // 1024 // 1024}MB")
        
        return file
    
    @staticmethod
    def validate_pagination_params():
        """验证分页参数"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        if page < 1:
            raise ValidationException("页码必须大于0")
        
        if per_page < 1 or per_page > 1000:
            raise ValidationException("每页记录数必须在1-1000之间")
        
        return page, per_page

class BatchValidator:
    """批量操作验证工具类"""
    
    @staticmethod
    def validate_batch_data(data, max_records=100):
        """验证批量数据"""
        if not data:
            raise ValidationException("批量数据不能为空")
        
        if not isinstance(data, list):
            raise ValidationException("批量数据必须是数组格式")
        
        if len(data) > max_records:
            raise ValidationException(f"批量操作记录数不能超过{max_records}条")
        
        return data
    
    @staticmethod
    def validate_batch_inventory_operation(records):
        """验证批量库存操作"""
        validated_records = []
        
        for i, record in enumerate(records):
            try:
                # 验证必填字段
                identification_code = FormValidator.validate_identification_code(
                    record.get('identification_code'), required=True
                )
                
                # 验证数量
                pallet_count = InputSanitizer.sanitize_integer(
                    record.get('pallet_count', 0), f"第{i+1}条记录的板数", min_value=0
                )
                package_count = InputSanitizer.sanitize_integer(
                    record.get('package_count', 0), f"第{i+1}条记录的件数", min_value=0
                )
                
                # 验证重量和体积
                weight = InputSanitizer.sanitize_number(
                    record.get('weight', 0), f"第{i+1}条记录的重量", min_value=0, decimal_places=2
                )
                volume = InputSanitizer.sanitize_number(
                    record.get('volume', 0), f"第{i+1}条记录的体积", min_value=0, decimal_places=2
                )
                
                validated_records.append({
                    'identification_code': identification_code,
                    'pallet_count': pallet_count,
                    'package_count': package_count,
                    'weight': weight,
                    'volume': volume
                })
                
            except ValidationException as e:
                raise ValidationException(f"第{i+1}条记录验证失败: {e.message}")
        
        return validated_records
