/**
 * 简单表格实现 - 用于替代jexcel库
 */

class SimpleTable {
    constructor(element, options) {
        this.element = typeof element === 'string' ? document.getElementById(element) : element;
        this.options = options || {};
        this.data = this.options.data || [];
        this.columns = this.options.columns || [];
        
        // 根据数据行数决定最小行数
        this.minRows = this.data.length > 0 ? this.data.length : (this.options.minDimensions && this.options.minDimensions[1]) || 10;
        
        // 确保数据至少有minRows行
        while (this.data.length < this.minRows) {
            const emptyRow = [];
            for (let i = 0; i < this.columns.length; i++) {
                emptyRow.push('');
            }
            this.data.push(emptyRow);
        }
        
        // 保存实例引用，便于全局访问
        window.simpleTableInstance = this;
        
        this.init();
    }
    
    init() {
        // 设置父容器样式，确保完全靠左
        if (this.element.parentElement) {
            this.element.parentElement.style.display = 'block';
            this.element.parentElement.style.marginLeft = '0';
            this.element.parentElement.style.paddingLeft = '0';
            this.element.parentElement.style.textAlign = 'left';
            this.element.parentElement.style.justifyContent = 'flex-start';
        }
        
        // 设置容器样式，确保靠左
        this.element.style.display = 'block';
        this.element.style.marginLeft = '0';
        this.element.style.paddingLeft = '0';
        this.element.style.width = '100%';
        this.element.style.maxWidth = '100%';
        this.element.style.overflowX = 'auto';
        this.element.style.textAlign = 'left';
        
        // 创建表格
        this.createTable();
        
        // 设置事件监听
        this.setupEvents();
        
        console.log('SimpleTable 初始化完成');
    }
    
    createTable() {
        // 清空容器
        this.element.innerHTML = '';
        
        // 创建表格元素 - 不使用包装容器，直接放置表格
        const table = document.createElement('table');
        table.className = 'simple-table table table-bordered table-striped';
        table.style.marginLeft = '0';
        table.style.marginRight = 'auto';
        table.style.width = '100%';
        table.style.textAlign = 'left';
        table.style.tableLayout = 'fixed'; // 改为fixed以确保列宽生效
        
        // 创建colgroup元素来设置列宽
        const colgroup = document.createElement('colgroup');
        
        // 创建表头
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        
        this.columns.forEach((column, index) => {
            // 创建col元素设置列宽
            const col = document.createElement('col');
            
            // 根据列标题调整特定列的宽度
            let width = column.width || 100;
            
            // 增加指定列的宽度
            const title = column.title || `列 ${index + 1}`;
            if (title.includes('入仓车牌')) {
                width = 150; // 设置宽度
                col.className = 'col-wide';
            } else if (title.includes('客户名称')) {
                width = 150; // 设置宽度
                col.className = 'col-wide';
            } else if (title.includes('出境模式')) {
                width = 150; // 设置宽度
                col.className = 'col-wide';
            } else if (title.includes('报关行')) {
                width = 150; // 设置宽度
                col.className = 'col-wide';
            } else if (title.includes('单据')) {
                width = 150; // 设置宽度
                col.className = 'col-wide';
            }
            
            // 设置列宽
            col.setAttribute('width', width);
            col.style.width = width + 'px';
            colgroup.appendChild(col);
            
            const th = document.createElement('th');
            // 检查标题是否包含星号，如果包含则设置红色样式
            if (title.includes('*')) {
                // 将星号标红
                const titleParts = title.split('*');
                th.innerHTML = titleParts[0] + '<span style="color:#ff0000;">*</span>' + (titleParts[1] || '');
            } else {
                th.innerHTML = title;
            }
            
            // 设置表头宽度
            th.setAttribute('width', width);
            th.style.width = width + 'px';
            th.style.minWidth = width + 'px';
            th.style.maxWidth = width + 'px';
            th.style.textAlign = column.align || 'left';
            th.dataset.column = index;
            // 添加标题数据属性用于CSS选择器
            th.dataset.title = title;
            
            // 根据列内容添加类名
            if (title.includes('入仓车牌')) {
                th.classList.add('column-inbound-plate');
            } else if (title.includes('客户名称')) {
                th.classList.add('column-customer-name');
            } else if (title.includes('出境模式')) {
                th.classList.add('column-exit-mode');
            } else if (title.includes('报关行')) {
                th.classList.add('column-customs-broker');
            }
            
            // 为特殊宽度列添加标记
            if (width === 150) {
                th.dataset.specialWidth = '150';
            }
            
            headerRow.appendChild(th);
        });
        
        // 将colgroup添加到表格
        table.appendChild(colgroup);
        
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        // 创建表体
        const tbody = document.createElement('tbody');
        
        this.data.forEach((row, rowIndex) => {
            const tr = document.createElement('tr');
            tr.dataset.row = rowIndex;
            
            row.forEach((cell, colIndex) => {
                const td = document.createElement('td');
                td.dataset.row = rowIndex;
                td.dataset.col = colIndex;
                
                // 设置单元格宽度与表头一致
                let width = this.columns[colIndex].width || 100;
                const title = this.columns[colIndex].title || `列 ${colIndex + 1}`;
                
                if (title.includes('入仓车牌')) {
                    width = 280;
                } else if (title.includes('客户名称')) {
                    width = 280;
                } else if (title.includes('出境模式')) {
                    width = 280;
                } else if (title.includes('报关行')) {
                    width = 280;
                }
                
                // 设置单元格宽度
                td.setAttribute('width', width);
                td.style.width = width + 'px';
                td.style.minWidth = width + 'px';
                td.style.maxWidth = width + 'px';
                
                // 为特殊宽度列添加标记
                if (width === 150) {
                    td.dataset.specialWidth = '150';
                }
                
                // 根据列类型设置单元格
                const column = this.columns[colIndex];
                if (column.type === 'calendar') {
                    const input = document.createElement('input');
                    input.type = 'date';
                    input.value = cell || '';
                    input.className = 'form-control';
                    input.style.padding = '2px';
                    input.style.height = 'auto';
                    input.style.width = '100%';
                    input.dataset.row = rowIndex;
                    input.dataset.col = colIndex;
                    input.addEventListener('change', (e) => {
                        this.data[rowIndex][colIndex] = e.target.value;
                    });
                    td.appendChild(input);
                } else if (column.type === 'numeric') {
                    const input = document.createElement('input');
                    input.type = 'number';
                    input.value = cell || '';
                    input.className = 'form-control';
                    input.style.padding = '2px';
                    input.style.height = 'auto';
                    input.style.width = '100%';
                    input.dataset.row = rowIndex;
                    input.dataset.col = colIndex;
                    input.addEventListener('change', (e) => {
                        this.data[rowIndex][colIndex] = e.target.value;
                    });
                    td.appendChild(input);
                } else {
                    const input = document.createElement('input');
                    input.type = 'text';
                    input.value = cell || '';
                    input.className = 'form-control';
                    input.style.padding = '2px';
                    input.style.height = 'auto';
                    input.style.width = '100%';
                    input.dataset.row = rowIndex;
                    input.dataset.col = colIndex;
                    input.addEventListener('change', (e) => {
                        this.data[rowIndex][colIndex] = e.target.value;
                    });
                    td.appendChild(input);
                }
                
                td.style.textAlign = column.align || 'left';
                tr.appendChild(td);
            });
            
            tbody.appendChild(tr);
        });
        
        table.appendChild(tbody);
        
        // 直接将表格添加到容器中，不使用包装容器
        this.element.appendChild(table);
        
        // 保存表格引用
        this.table = table;
        
        // 直接在DOM中设置列宽
        this.setColumnWidths();
    }
    
    // 设置列宽
    setColumnWidths() {
        // 直接在DOM中设置列宽
        const specialColumns = ['入仓车牌', '客户名称', '出境模式', '报关行', '单据'];
        
        // 处理每一列
        this.columns.forEach((column, index) => {
            const title = column.title || '';
            let width = column.width || 100;
            
            // 检查是否是特殊宽度的列
            specialColumns.forEach(specialCol => {
                if (title.includes(specialCol)) {
                    width = 150; // 修改为150px
                }
            });
            
            // 设置colgroup列宽
            const cols = this.table.querySelectorAll('colgroup col');
            if (cols[index]) {
                cols[index].style.width = width + 'px';
                cols[index].setAttribute('width', width);
            }
            
            // 设置表头列宽
            const ths = this.table.querySelectorAll('th');
            if (ths[index]) {
                ths[index].style.width = width + 'px';
                ths[index].style.minWidth = width + 'px';
                ths[index].style.maxWidth = width + 'px';
                ths[index].setAttribute('width', width);
            }
            
            // 设置单元格列宽
            const cells = this.table.querySelectorAll(`td[data-col="${index}"]`);
            cells.forEach(cell => {
                cell.style.width = width + 'px';
                cell.style.minWidth = width + 'px';
                cell.style.maxWidth = width + 'px';
                cell.setAttribute('width', width);
            });
        });
    }
    
    setupEvents() {
        // 处理按钮事件
        const container = this.element.closest('.table-container') || document.body;
        
        // 查找表格相关的按钮
        const addRowBtn = container.querySelector('.btn-add-row');
        if (addRowBtn) {
            addRowBtn.addEventListener('click', () => {
                this.insertRow(1, 0);
                console.log('添加行');
            });
        }
        
        const removeRowBtn = container.querySelector('.btn-remove-row');
        if (removeRowBtn) {
            removeRowBtn.addEventListener('click', () => {
                const selectedRows = this.getSelectedRows();
                if (selectedRows.length > 0) {
                    // 从大到小排序，避免删除过程中索引变化
                    selectedRows.sort((a, b) => b - a).forEach(rowIndex => {
                        this.deleteRow(rowIndex);
                    });
                } else {
                    alert('请先选择要删除的行');
                }
                console.log('删除选中行');
            });
        }
        
        const saveBtn = container.querySelector('.btn-save');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => {
                // 保存数据逻辑
                if (typeof this.options.onSave === 'function') {
                    this.options.onSave(this.getData());
                } else {
                    console.log('保存数据:', this.getData());
                }
            });
        }
        
        // 添加表格单元格选择事件
        if (this.table) {
            this.table.addEventListener('click', (e) => {
                const td = e.target.closest('td');
                if (td) {
                    // 清除之前选中的单元格
                    this.table.querySelectorAll('.selected').forEach(cell => {
                        cell.classList.remove('selected');
                    });
                    // 标记当前单元格为选中
                    td.classList.add('selected');
                    
                    // 触发选择事件
                    if (typeof this.options.onSelection === 'function') {
                        const row = parseInt(td.dataset.row, 10);
                        const col = parseInt(td.dataset.col, 10);
                        this.options.onSelection(row, col, td);
                    }
                }
            });
        }
    }
    
    // 获取数据
    getData() {
        return this.data;
    }
    
    // 设置数据
    setData(data) {
        this.data = data;
        // 使用实际数据行数设置表格
        this.minRows = data.length > 0 ? data.length : 10;
        this.createTable(); // 重新创建表格
    }
    
    // 获取选中的行
    getSelectedRows() {
        const selectedRows = new Set();
        if (this.table) {
            const selectedCells = this.table.querySelectorAll('td.selected');
            selectedCells.forEach(cell => {
                const row = parseInt(cell.dataset.row, 10);
                if (!isNaN(row)) {
                    selectedRows.add(row);
                }
            });
        }
        return Array.from(selectedRows);
    }
    
    // 插入行
    insertRow(numRows, rowIndex) {
        rowIndex = rowIndex !== undefined ? rowIndex : 0;
        
        for (let i = 0; i < numRows; i++) {
            const newRow = [];
            for (let j = 0; j < this.columns.length; j++) {
                newRow.push('');
            }
            this.data.splice(rowIndex, 0, newRow);
        }
        
        this.createTable(); // 重新创建表格
    }
    
    // 删除行
    deleteRow(rowIndex) {
        if (rowIndex >= 0 && rowIndex < this.data.length) {
            this.data.splice(rowIndex, 1);
            this.createTable(); // 重新创建表格
        }
    }
    
    // 设置单元格值
    setValueFromCoords(col, row, value) {
        if (row >= 0 && row < this.data.length && col >= 0 && col < this.columns.length) {
            this.data[row][col] = value;
            
            // 更新UI
            const cell = this.table.querySelector(`td[data-row="${row}"][data-col="${col}"] input`);
            if (cell) {
                cell.value = value;
            }
        }
    }
    
    // 强制刷新表格以应用新的列宽
    refreshTable() {
        this.createTable(); // 重新创建表格以应用最新的样式设置
    }
}

// 添加全局方法用于强制刷新表格
window.refreshSimpleTable = function() {
    if (window.simpleTableInstance) {
        window.simpleTableInstance.refreshTable();
    }
};

// 导出
window.SimpleTable = SimpleTable; 