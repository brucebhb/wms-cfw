#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨平台打印机管理工具
支持Windows、Linux、macOS
"""

import os
import sys
import subprocess
import platform
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class CrossPlatformPrinter:
    """跨平台打印机管理类"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.is_windows = self.system == 'windows'
        self.is_linux = self.system == 'linux'
        self.is_macos = self.system == 'darwin'
        
    def get_printers(self) -> List[Dict[str, any]]:
        """获取系统打印机列表"""
        try:
            if self.is_windows:
                return self._get_windows_printers()
            elif self.is_linux:
                return self._get_linux_printers()
            elif self.is_macos:
                return self._get_macos_printers()
            else:
                logger.warning(f"不支持的操作系统: {self.system}")
                return self._get_fallback_printers()
        except Exception as e:
            logger.error(f"获取打印机列表失败: {e}")
            return self._get_fallback_printers()
    
    def _get_windows_printers(self) -> List[Dict[str, any]]:
        """获取Windows打印机列表"""
        printers = []
        
        try:
            # 方法1: 使用win32print (如果可用)
            import win32print
            
            default_printer = win32print.GetDefaultPrinter()
            printer_list = win32print.EnumPrinters(
                win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            )
            
            for printer_info in printer_list:
                printer_name = printer_info[2]
                printers.append({
                    'name': printer_name,
                    'isDefault': printer_name == default_printer,
                    'status': 'available',
                    'type': 'local' if printer_info[0] & win32print.PRINTER_ENUM_LOCAL else 'network'
                })
                
        except ImportError:
            # 方法2: 使用wmic命令
            try:
                output = subprocess.check_output(
                    'wmic printer get name,default /format:csv', 
                    shell=True, 
                    text=True
                )
                lines = output.strip().split('\n')[1:]  # 跳过标题行
                
                for line in lines:
                    if line.strip():
                        parts = line.split(',')
                        if len(parts) >= 3:
                            is_default = parts[1].strip().lower() == 'true'
                            printer_name = parts[2].strip()
                            if printer_name:
                                printers.append({
                                    'name': printer_name,
                                    'isDefault': is_default,
                                    'status': 'available',
                                    'type': 'unknown'
                                })
            except Exception as e:
                logger.error(f"使用wmic获取打印机失败: {e}")
                
        return printers
    
    def _get_linux_printers(self) -> List[Dict[str, any]]:
        """获取Linux打印机列表"""
        printers = []
        
        try:
            # 方法1: 使用lpstat命令
            result = subprocess.run(['lpstat', '-p'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.startswith('printer '):
                        parts = line.split()
                        if len(parts) >= 2:
                            printer_name = parts[1]
                            status = 'available' if 'idle' in line else 'busy'
                            printers.append({
                                'name': printer_name,
                                'isDefault': False,  # 稍后确定默认打印机
                                'status': status,
                                'type': 'cups'
                            })
            
            # 获取默认打印机
            try:
                result = subprocess.run(['lpstat', '-d'], capture_output=True, text=True)
                if result.returncode == 0:
                    output = result.stdout.strip()
                    if 'system default destination:' in output:
                        default_name = output.split('system default destination:')[1].strip()
                        for printer in printers:
                            if printer['name'] == default_name:
                                printer['isDefault'] = True
                                break
            except Exception:
                pass
                
        except FileNotFoundError:
            # 方法2: 使用lpr -P命令检查
            try:
                result = subprocess.run(['lpr', '-P', '?'], capture_output=True, text=True)
                # 解析输出获取打印机列表
            except Exception:
                pass
        
        # 方法3: 检查CUPS配置文件
        if not printers:
            try:
                cups_printers_dir = '/etc/cups/printers.conf'
                if os.path.exists(cups_printers_dir):
                    with open(cups_printers_dir, 'r') as f:
                        content = f.read()
                        # 解析CUPS配置文件
                        import re
                        printer_names = re.findall(r'<Printer\s+([^>]+)>', content)
                        for name in printer_names:
                            printers.append({
                                'name': name,
                                'isDefault': False,
                                'status': 'unknown',
                                'type': 'cups'
                            })
            except Exception as e:
                logger.error(f"读取CUPS配置失败: {e}")
        
        return printers
    
    def _get_macos_printers(self) -> List[Dict[str, any]]:
        """获取macOS打印机列表"""
        printers = []
        
        try:
            # 使用lpstat命令
            result = subprocess.run(['lpstat', '-p'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.startswith('printer '):
                        parts = line.split()
                        if len(parts) >= 2:
                            printer_name = parts[1]
                            status = 'available' if 'idle' in line else 'busy'
                            printers.append({
                                'name': printer_name,
                                'isDefault': False,
                                'status': status,
                                'type': 'cups'
                            })
            
            # 获取默认打印机
            try:
                result = subprocess.run(['lpstat', '-d'], capture_output=True, text=True)
                if result.returncode == 0 and 'system default destination:' in result.stdout:
                    default_name = result.stdout.split('system default destination:')[1].strip()
                    for printer in printers:
                        if printer['name'] == default_name:
                            printer['isDefault'] = True
                            break
            except Exception:
                pass
                
        except Exception as e:
            logger.error(f"获取macOS打印机失败: {e}")
            
        return printers
    
    def _get_fallback_printers(self) -> List[Dict[str, any]]:
        """备用打印机列表（当无法检测到真实打印机时）"""
        return [
            {
                'name': 'PDF打印机',
                'isDefault': True,
                'status': 'available',
                'type': 'virtual',
                'description': '生成PDF文件'
            },
            {
                'name': '系统默认打印机',
                'isDefault': False,
                'status': 'unknown',
                'type': 'system',
                'description': '使用系统默认设置'
            }
        ]
    
    def get_default_printer(self) -> Optional[str]:
        """获取默认打印机名称"""
        printers = self.get_printers()
        for printer in printers:
            if printer.get('isDefault'):
                return printer['name']
        
        # 如果没有找到默认打印机，返回第一个可用的
        if printers:
            return printers[0]['name']
        
        return None
    
    def print_file(self, file_path: str, printer_name: str = None, copies: int = 1) -> bool:
        """打印文件"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                return False
            
            if printer_name is None:
                printer_name = self.get_default_printer()
            
            if self.is_windows:
                return self._print_file_windows(file_path, printer_name, copies)
            elif self.is_linux:
                return self._print_file_linux(file_path, printer_name, copies)
            elif self.is_macos:
                return self._print_file_macos(file_path, printer_name, copies)
            else:
                logger.error(f"不支持的操作系统: {self.system}")
                return False
                
        except Exception as e:
            logger.error(f"打印文件失败: {e}")
            return False
    
    def _print_file_windows(self, file_path: str, printer_name: str, copies: int) -> bool:
        """Windows打印文件"""
        try:
            # 使用Windows的print命令
            cmd = f'print /D:"{printer_name}" "{file_path}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Windows打印失败: {e}")
            return False
    
    def _print_file_linux(self, file_path: str, printer_name: str, copies: int) -> bool:
        """Linux打印文件"""
        try:
            cmd = ['lpr']
            if printer_name and printer_name != 'PDF打印机':
                cmd.extend(['-P', printer_name])
            if copies > 1:
                cmd.extend(['-#', str(copies)])
            cmd.append(file_path)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Linux打印失败: {e}")
            return False
    
    def _print_file_macos(self, file_path: str, printer_name: str, copies: int) -> bool:
        """macOS打印文件"""
        try:
            cmd = ['lpr']
            if printer_name and printer_name != 'PDF打印机':
                cmd.extend(['-P', printer_name])
            if copies > 1:
                cmd.extend(['-#', str(copies)])
            cmd.append(file_path)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"macOS打印失败: {e}")
            return False

# 全局实例
printer_manager = CrossPlatformPrinter()

def get_system_printers():
    """获取系统打印机列表的便捷函数"""
    return printer_manager.get_printers()

def get_default_printer():
    """获取默认打印机的便捷函数"""
    return printer_manager.get_default_printer()

def print_file(file_path: str, printer_name: str = None, copies: int = 1):
    """打印文件的便捷函数"""
    return printer_manager.print_file(file_path, printer_name, copies)
