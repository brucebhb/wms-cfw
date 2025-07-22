/**
 * 表格列宽调整组件
 * 参考车夫网TMS系统的实现风格
 */
(function() {
    // 默认配置
    const DEFAULT_CONFIG = {
        minWidth: 50,       // 列的最小宽度
        headerHeight: 30,   // 表头高度
        resizerWidth: 8,    // 调整器宽度
        storagePrefix: 'table-col-width-',  // 本地存储前缀
        persistColumnWidths: true           // 是否持久化列宽
    };
    
    // 表格列宽调整类
    class TableColumnResizer {
        constructor(tableSelector, options = {}) {
            // 合并配置
            this.config = {...DEFAULT_CONFIG, ...options};
            
            // 获取表格元素
            this.table = typeof tableSelector === 'string' 
                ? document.querySelector(tableSelector) 
                : tableSelector;
                
            if (!this.table) {
                console.error('未找到表格元素:', tableSelector);
                return;
            }
            
            // 生成表格 ID
            this.tableId = this.table.id || `table-${Math.random().toString(36).substr(2, 9)}`;
            
            // 初始化
            this.init();
        }
        
        // 初始化
        init() {
            // 添加必要的样式类
            this.table.classList.add('table-resizable');
            
            // 获取表头单元格
            const headers = this.table.querySelectorAll('thead th');
            if (headers.length === 0) {
                console.error('表格没有表头:', this.tableId);
                return;
            }
            
            // 加载已保存的列宽
            this.loadColumnWidths();
            
            // 为每个表头添加调整器
            headers.forEach((header, index) => {
                if (index < headers.length - 1) {  // 最后一列不添加调整器
                    this.addResizer(header, index);
                }
            });
        }
        
        // 添加列宽调整器
        addResizer(header, index) {
            // 创建调整器元素
            const resizer = document.createElement('div');
            resizer.classList.add('resizer');
            
            // 设置拖动状态变量
            let startX, startWidth, nextStartWidth;
            
            // 设置拖动开始事件
            resizer.addEventListener('mousedown', e => {
                startX = e.pageX;
                const headerRect = header.getBoundingClientRect();
                startWidth = headerRect.width;
                
                // 获取下一列的宽度
                const nextHeader = header.nextElementSibling;
                const nextHeaderRect = nextHeader.getBoundingClientRect();
                nextStartWidth = nextHeaderRect.width;
                
                // 添加拖动样式
                resizer.classList.add('resizing');
                document.body.style.cursor = 'col-resize';
                
                // 添加全局拖动事件
                document.addEventListener('mousemove', handleMouseMove);
                document.addEventListener('mouseup', handleMouseUp);
                
                e.preventDefault();
            });
            
            // 处理鼠标移动
            const handleMouseMove = e => {
                const dx = e.pageX - startX;
                
                // 应用新宽度（考虑最小宽度限制）
                const newWidth = Math.max(this.config.minWidth, startWidth + dx);
                header.style.width = `${newWidth}px`;
                header.style.minWidth = `${newWidth}px`;
                
                // 可选：调整数据单元格宽度
                this.adjustColumnCells(index, newWidth);
            };
            
            // 处理鼠标释放
            const handleMouseUp = () => {
                // 移除拖动样式
                resizer.classList.remove('resizing');
                document.body.style.cursor = '';
                
                // 移除全局事件
                document.removeEventListener('mousemove', handleMouseMove);
                document.removeEventListener('mouseup', handleMouseUp);
                
                // 获取最终宽度
                const finalWidth = parseInt(header.style.width);
                
                // 保存列宽
                if (this.config.persistColumnWidths) {
                    this.saveColumnWidth(index, finalWidth);
                }
                
                // 触发列宽调整完成事件
                this.triggerResizeEvent(index, finalWidth);
            };
            
            // 添加调整器到表头
            header.appendChild(resizer);
            header.style.position = 'relative';
            
            // 设置初始宽度
            if (this.columnWidths && this.columnWidths[index]) {
                const width = this.columnWidths[index];
                header.style.width = `${width}px`;
                header.style.minWidth = `${width}px`;
                
                // 调整数据单元格宽度
                this.adjustColumnCells(index, width);
            }
        }
        
        // 调整列的所有单元格宽度
        adjustColumnCells(columnIndex, width) {
            const rows = this.table.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const cell = row.cells[columnIndex];
                if (cell) {
                    cell.style.width = `${width}px`;
                    cell.style.minWidth = `${width}px`;
                    cell.style.maxWidth = `${width}px`;
                }
            });
        }
        
        // 保存列宽到本地存储
        saveColumnWidth(columnIndex, width) {
            // 读取现有的列宽或创建新的
            let columnWidths = this.columnWidths || {};
            
            // 更新指定列的宽度
            columnWidths[columnIndex] = width;
            
            // 保存到本地存储
            localStorage.setItem(this.getStorageKey(), JSON.stringify(columnWidths));
            
            // 更新实例属性
            this.columnWidths = columnWidths;
        }
        
        // 加载保存的列宽
        loadColumnWidths() {
            const storageKey = this.getStorageKey();
            const savedData = localStorage.getItem(storageKey);
            
            if (savedData) {
                try {
                    this.columnWidths = JSON.parse(savedData);
                } catch (e) {
                    console.error('解析保存的列宽数据失败:', e);
                    this.columnWidths = {};
                }
            } else {
                this.columnWidths = {};
            }
        }
        
        // 获取本地存储键
        getStorageKey() {
            return `${this.config.storagePrefix}${this.tableId}`;
        }
        
        // 触发列宽调整完成事件
        triggerResizeEvent(columnIndex, width) {
            const event = new CustomEvent('column-resized', {
                detail: {
                    columnIndex: columnIndex,
                    width: width,
                    table: this.table,
                    tableId: this.tableId
                }
            });
            
            this.table.dispatchEvent(event);
        }
        
        // 重置列宽
        resetColumnWidths() {
            // 清除本地存储
            localStorage.removeItem(this.getStorageKey());
            this.columnWidths = {};
            
            // 重置表格样式
            const headers = this.table.querySelectorAll('thead th');
            headers.forEach((header, index) => {
                header.style.width = '';
                header.style.minWidth = '';
                
                // 重置单元格宽度
                const rows = this.table.querySelectorAll('tbody tr');
                rows.forEach(row => {
                    const cell = row.cells[index];
                    if (cell) {
                        cell.style.width = '';
                        cell.style.minWidth = '';
                        cell.style.maxWidth = '';
                    }
                });
            });
        }
    }
    
    // 注册到全局
    window.TableColumnResizer = TableColumnResizer;
    
    // 自动初始化带有data-resizable属性的表格
    document.addEventListener('DOMContentLoaded', () => {
        const tables = document.querySelectorAll('table[data-resizable="true"]');
        tables.forEach(table => {
            new TableColumnResizer(table);
        });
    });
})(); 