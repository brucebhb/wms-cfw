/**
 * 表格列宽调整功能
 * 基于原生JavaScript实现，无需依赖其他库
 */
(function() {
  // 创建并附加调整器元素到每个表头
  function createResizers(table) {
    // 添加表格容器类
    table.classList.add('table-resizable');
    
    // 获取所有表头
    const headers = table.querySelectorAll('thead th');
    
    // 列宽存储键
    const tableId = table.getAttribute('id') || 'resizable-table';
    
    // 为每个表头添加调整器
    headers.forEach((header, index) => {
      // 最后一列不需要调整器
      if (index < headers.length - 1) {
        const resizer = document.createElement('div');
        resizer.classList.add('resizer');
        
        // 初始化拖动变量
        let startX, startWidth, nextStartWidth;
        
        // 设置拖动事件
        resizer.addEventListener('mousedown', e => {
          startX = e.pageX;
          const headerRect = header.getBoundingClientRect();
          startWidth = headerRect.width;
          
          // 获取下一个表头的宽度
          const nextHeader = header.nextElementSibling;
          const nextHeaderRect = nextHeader.getBoundingClientRect();
          nextStartWidth = nextHeaderRect.width;
          
          // 添加拖动状态
          resizer.classList.add('resizing');
          
          // 添加全局拖动事件
          document.addEventListener('mousemove', handleMouseMove);
          document.addEventListener('mouseup', handleMouseUp);
          
          e.preventDefault();
        });
        
        // 处理鼠标移动
        function handleMouseMove(e) {
          const dx = e.pageX - startX;
          
          // 限制最小宽度，为单据列设置更大的最小宽度
          const minWidth = header.innerText.trim() === '单据' ? 100 : 50;
          const newWidth = Math.max(minWidth, startWidth + dx);
          header.style.width = newWidth + 'px';
          header.style.minWidth = newWidth + 'px';
          
          // 保存列宽到本地存储
          saveColumnWidth(tableId, index, newWidth);
        }
        
        // 处理鼠标释放
        function handleMouseUp() {
          resizer.classList.remove('resizing');
          document.removeEventListener('mousemove', handleMouseMove);
          document.removeEventListener('mouseup', handleMouseUp);
        }
        
        // 附加调整器到表头
        header.appendChild(resizer);
        header.style.position = 'relative';
        
        // 从本地存储加载列宽
        loadColumnWidth(tableId, index, header);
        
        // 为单据列设置默认最小宽度
        if (header.innerText.trim() === '单据' && (!header.style.width || parseInt(header.style.width) < 100)) {
          header.style.width = '100px';
          header.style.minWidth = '100px';
          saveColumnWidth(tableId, index, 100);
        }
      }
    });
  }
  
  // 保存列宽到本地存储
  function saveColumnWidth(tableId, columnIndex, width) {
    // 获取现有的列宽设置或创建新的
    let columnWidths = localStorage.getItem(tableId + '-column-widths');
    columnWidths = columnWidths ? JSON.parse(columnWidths) : {};
    
    // 更新列宽
    columnWidths[columnIndex] = width;
    
    // 保存回本地存储
    localStorage.setItem(tableId + '-column-widths', JSON.stringify(columnWidths));
  }
  
  // 从本地存储加载列宽
  function loadColumnWidth(tableId, columnIndex, header) {
    const columnWidths = localStorage.getItem(tableId + '-column-widths');
    if (columnWidths) {
      const widths = JSON.parse(columnWidths);
      if (widths[columnIndex]) {
        const width = widths[columnIndex];
        // 确保单据列的宽度至少为100px
        if (header.innerText.trim() === '单据' && width < 100) {
          header.style.width = '100px';
          header.style.minWidth = '100px';
          saveColumnWidth(tableId, columnIndex, 100);
        } else {
          header.style.width = width + 'px';
          header.style.minWidth = width + 'px';
        }
      }
    }
  }
  
  // 初始化所有可调整列宽的表格
  function init() {
    const tables = document.querySelectorAll('table.resizable');
    tables.forEach(table => {
      createResizers(table);
    });
  }
  
  // DOM加载完成后初始化
  document.addEventListener('DOMContentLoaded', init);
  
  // 暴露到全局，以便手动初始化
  window.initResizableTable = function(tableSelector) {
    const table = document.querySelector(tableSelector);
    if (table) {
      createResizers(table);
    }
  };
})(); 