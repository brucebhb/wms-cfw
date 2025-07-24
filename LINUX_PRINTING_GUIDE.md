# 🐧 Linux打印功能完整指南

## 📋 概述

您的仓储管理系统已经完全支持Linux环境下的打印功能。系统采用跨平台设计，可以在Windows、Linux和macOS上无缝运行，并提供完整的打印机管理和标签打印功能。

## ✅ Linux打印功能特性

### 🎯 **核心功能**
- ✅ **自动打印机检测** - 支持CUPS打印系统
- ✅ **跨平台兼容** - Windows/Linux/macOS统一接口
- ✅ **PDF标签生成** - 支持中文字体和自定义格式
- ✅ **批量打印** - 支持多份打印和批量标签
- ✅ **打印机状态监控** - 实时检测打印机可用性
- ✅ **默认打印机管理** - 自动识别系统默认打印机

### 🔧 **技术实现**
- **CUPS集成** - 使用Linux标准打印系统
- **命令行支持** - lpstat、lpr、lpadmin命令
- **Python模块** - cups-python原生支持
- **PDF生成** - reportlab库生成高质量标签
- **错误处理** - 完善的异常处理和降级方案

## 🛠️ Linux环境配置

### 1. **安装CUPS打印系统**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install cups cups-client

# CentOS/RHEL
sudo yum install cups cups-client

# 或者使用dnf (较新版本)
sudo dnf install cups cups-client
```

### 2. **启动CUPS服务**
```bash
# 启动CUPS服务
sudo systemctl start cups

# 设置开机自启
sudo systemctl enable cups

# 检查服务状态
sudo systemctl status cups
```

### 3. **安装Python依赖**
```bash
# 安装cups-python (Linux环境自动安装)
pip install cups-python

# 安装PDF生成库
pip install reportlab

# 或者使用项目requirements.txt
pip install -r requirements.txt
```

### 4. **配置打印机**
```bash
# 查看可用打印机
lpstat -p

# 查看默认打印机
lpstat -d

# 添加打印机 (需要管理员权限)
sudo lpadmin -p printer_name -E -v device_uri

# 设置默认打印机
lpoptions -d printer_name
```

## 🧪 功能测试

### **运行测试脚本**
```bash
# 在项目根目录运行
python3 test_linux_printing.py
```

**测试内容包括：**
- ✅ 系统环境检查
- ✅ CUPS安装验证
- ✅ cups-python模块测试
- ✅ 打印机检测功能
- ✅ PDF生成功能
- ✅ 跨平台打印管理器
- ✅ 实际打印功能测试

## 📊 打印机管理API

### **获取打印机列表**
```python
from app.utils.cross_platform_printer import get_system_printers

# 获取所有打印机
printers = get_system_printers()

# 返回格式
[
    {
        'name': 'HP_LaserJet_P1005',
        'isDefault': True,
        'status': 'available',  # available, busy, offline
        'type': 'cups'
    },
    ...
]
```

### **获取默认打印机**
```python
from app.utils.cross_platform_printer import get_default_printer

default_printer = get_default_printer()
print(f"默认打印机: {default_printer}")
```

### **打印文件**
```python
from app.utils.cross_platform_printer import CrossPlatformPrinter

printer_manager = CrossPlatformPrinter()

# 打印PDF文件
success = printer_manager.print_file(
    file_path='/path/to/label.pdf',
    printer_name='HP_LaserJet_P1005',
    copies=2
)
```

## 🏷️ 标签生成功能

### **生成单个标签**
```python
from app.utils.pdf_label_generator import generate_simple_label

pdf_path = generate_simple_label(
    customer_name='测试客户',
    identification_code='PH/测试客户/粤B12345/20250724/001',
    plate_number='粤B12345',
    package_count=10,
    pallet_count=2,
    weight=500.5,
    volume=2.5
)
```

### **批量生成标签**
```python
from app.utils.pdf_label_generator import generate_label_pdf

labels_data = [
    {
        'customer_name': '客户A',
        'identification_code': 'PH/客户A/粤B11111/20250724/001',
        'plate_number': '粤B11111',
        'package_count': 5,
        'pallet_count': 1,
        'weight': 250.0,
        'volume': 1.2
    },
    # ... 更多标签数据
]

pdf_path = generate_label_pdf(labels_data, copies=2)
```

## 🔧 Linux特定实现

### **打印机检测方法**
```python
def _get_linux_printers(self):
    """Linux打印机检测的多种方法"""
    
    # 方法1: 使用lpstat命令
    result = subprocess.run(['lpstat', '-p'], capture_output=True, text=True)
    
    # 方法2: 使用cups-python模块
    import cups
    conn = cups.Connection()
    printers = conn.getPrinters()
    
    # 方法3: 读取CUPS配置文件
    with open('/etc/cups/printers.conf', 'r') as f:
        content = f.read()
```

### **打印命令构建**
```python
def _print_file_linux(self, file_path, printer_name, copies):
    """Linux打印命令"""
    cmd = ['lpr']
    
    # 指定打印机
    if printer_name and printer_name != 'PDF打印机':
        cmd.extend(['-P', printer_name])
    
    # 指定份数
    if copies > 1:
        cmd.extend(['-#', str(copies)])
    
    # 添加文件路径
    cmd.append(file_path)
    
    # 执行打印
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0
```

## 🚀 Web界面集成

### **前端打印机选择**
```javascript
// 获取打印机列表
fetch('/api/printers')
    .then(response => response.json())
    .then(printers => {
        const select = document.getElementById('printer-select');
        printers.forEach(printer => {
            const option = document.createElement('option');
            option.value = printer.name;
            option.textContent = `${printer.name}${printer.isDefault ? ' (默认)' : ''}`;
            if (printer.isDefault) option.selected = true;
            select.appendChild(option);
        });
    });
```

### **标签打印接口**
```javascript
// 打印标签
function printLabels(recordIds, printerName, copies) {
    fetch('/api/print_labels', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            record_ids: recordIds,
            printer_name: printerName,
            copies: copies
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('打印任务已发送', 'success');
        } else {
            showNotification('打印失败: ' + data.message, 'error');
        }
    });
}
```

## 🔍 故障排除

### **常见问题**

#### 1. **找不到打印机**
```bash
# 检查CUPS服务
sudo systemctl status cups

# 重启CUPS服务
sudo systemctl restart cups

# 检查打印机连接
lpstat -p
```

#### 2. **权限问题**
```bash
# 将用户添加到lpadmin组
sudo usermod -a -G lpadmin $USER

# 重新登录或重启
```

#### 3. **cups-python安装失败**
```bash
# 安装开发包
sudo apt-get install libcups2-dev

# 重新安装
pip install --force-reinstall cups-python
```

#### 4. **PDF生成失败**
```bash
# 安装字体包
sudo apt-get install fonts-noto-cjk

# 检查reportlab
python3 -c "import reportlab; print('reportlab可用')"
```

### **调试方法**

#### 1. **启用详细日志**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 2. **测试打印命令**
```bash
# 手动测试打印
echo "测试打印" | lpr -P printer_name

# 检查打印队列
lpq
```

#### 3. **检查CUPS日志**
```bash
# 查看CUPS错误日志
sudo tail -f /var/log/cups/error_log

# 查看访问日志
sudo tail -f /var/log/cups/access_log
```

## 📈 性能优化

### **打印机缓存**
- 系统会缓存打印机列表，减少重复查询
- 定期刷新打印机状态
- 异步处理打印任务

### **PDF优化**
- 使用压缩算法减小PDF文件大小
- 批量生成时复用字体资源
- 临时文件自动清理

### **错误恢复**
- 多种打印机检测方法降级
- 打印失败时的重试机制
- 详细的错误日志记录

## 🎯 最佳实践

1. **生产环境部署**
   - 使用专用打印服务器
   - 配置网络打印机
   - 设置打印队列监控

2. **安全考虑**
   - 限制打印机访问权限
   - 审计打印日志
   - 防止打印队列溢出

3. **维护建议**
   - 定期清理临时文件
   - 监控打印机状态
   - 备份CUPS配置

## 📞 技术支持

如遇到Linux打印问题，请：
1. 运行 `python3 test_linux_printing.py` 进行诊断
2. 检查CUPS服务状态
3. 查看应用日志文件
4. 确认打印机驱动安装

您的仓储管理系统在Linux环境下具备完整的打印功能支持！
