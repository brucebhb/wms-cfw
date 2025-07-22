/**
 * 后端仓入库页面增强脚本
 * 专门优化前端仓发货批次列表的显示效果
 */

(function() {
    'use strict';
    
    // 等待页面加载完成
    document.addEventListener('DOMContentLoaded', function() {
        enhanceBackendInboundPage();
    });
    
    function enhanceBackendInboundPage() {
        console.log('🔧 开始优化后端仓入库页面');
        
        // 检查是否是后端仓入库页面
        if (!isBackendInboundPage()) {
            return;
        }
        
        // 为页面添加标识类
        document.body.classList.add('backend-inbound-page');
        
        // 优化表格显示
        enhanceTables();
        
        // 监听动态加载的表格
        observeTableChanges();
        
        console.log('✅ 后端仓入库页面优化完成');
    }
    
    function isBackendInboundPage() {
        // 检查URL或页面内容来确定是否是后端仓入库页面
        const url = window.location.pathname;
        const pageContent = document.body.textContent;
        
        return url.includes('backend') && url.includes('inbound') ||
               pageContent.includes('前端仓发货批次') ||
               pageContent.includes('待接收') ||
               document.querySelector('.card-title')?.textContent?.includes('前端仓发货批次');
    }
    
    function enhanceTables() {
        // 查找所有可能的表格
        const tables = document.querySelectorAll('table');
        
        tables.forEach(table => {
            enhanceTable(table);
        });
        
        // 特别处理包含"待接收"或"前端仓发货批次"的表格
        const batchTables = Array.from(tables).filter(table => {
            const tableText = table.textContent;
            return tableText.includes('待接收') || 
                   tableText.includes('前端仓发货批次') ||
                   tableText.includes('识别编码') ||
                   tableText.includes('批次号');
        });
        
        batchTables.forEach(table => {
            enhanceBatchTable(table);
        });
    }
    
    function enhanceTable(table) {
        // 为表格添加优化类
        table.classList.add('pending-batches-table');
        
        // 优化表头
        const headers = table.querySelectorAll('th');
        headers.forEach(th => {
            th.style.fontSize = '14px';
            th.style.fontWeight = '600';
            th.style.padding = '12px 8px';
            th.style.backgroundColor = '#f8f9fa';
        });
        
        // 优化表格单元格
        const cells = table.querySelectorAll('td');
        cells.forEach(td => {
            td.style.fontSize = '14px';
            td.style.padding = '12px 8px';
            td.style.lineHeight = '1.6';
            td.style.verticalAlign = 'middle';
        });
    }
    
    function enhanceBatchTable(table) {
        console.log('🎯 优化批次表格');
        
        // 为批次表格添加特殊类
        table.classList.add('batch-list-table');
        
        // 查找识别编码列并特别优化
        const rows = table.querySelectorAll('tr');
        rows.forEach(row => {
            const cells = row.querySelectorAll('td, th');
            cells.forEach((cell, index) => {
                const cellText = cell.textContent.trim();
                
                // 识别编码列
                if (cellText.includes('/') && cellText.length > 10) {
                    cell.classList.add('identification-code');
                    cell.style.fontSize = '15px';
                    cell.style.fontWeight = '500';
                    cell.style.wordWrap = 'break-word';
                    cell.style.whiteSpace = 'normal';
                }
                
                // 批次号列
                if (cellText.match(/^[A-Z]{2}\d+/) || cell.textContent.includes('批次')) {
                    cell.classList.add('batch-number');
                    cell.style.fontSize = '14px';
                    cell.style.fontWeight = '500';
                }
                
                // 数量相关列
                if (cellText.match(/^\d+$/) && parseInt(cellText) > 0) {
                    cell.classList.add('quantity-column');
                    cell.style.textAlign = 'center';
                    cell.style.fontWeight = '500';
                }
                
                // 操作按钮列
                if (cell.querySelector('button') || cell.querySelector('.btn')) {
                    cell.classList.add('action-buttons');
                    cell.style.padding = '8px 4px';
                    
                    // 优化按钮样式
                    const buttons = cell.querySelectorAll('button, .btn');
                    buttons.forEach(btn => {
                        btn.style.fontSize = '12px';
                        btn.style.padding = '4px 8px';
                        btn.style.margin = '1px';
                    });
                }
            });
        });
        
        // 添加悬停效果
        const tableRows = table.querySelectorAll('tbody tr');
        tableRows.forEach(row => {
            row.addEventListener('mouseenter', function() {
                this.style.backgroundColor = '#f8f9fa';
            });
            
            row.addEventListener('mouseleave', function() {
                this.style.backgroundColor = '';
            });
        });
    }
    
    function observeTableChanges() {
        // 监听DOM变化，处理动态加载的表格
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            // 检查新添加的表格
                            const newTables = node.querySelectorAll ? 
                                node.querySelectorAll('table') : [];
                            
                            if (node.tagName === 'TABLE') {
                                enhanceTable(node);
                            }
                            
                            newTables.forEach(table => {
                                enhanceTable(table);
                            });
                        }
                    });
                }
            });
        });
        
        // 开始监听
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        console.log('👀 已启动表格变化监听');
    }
    
    // 提供手动刷新功能
    window.refreshTableStyles = function() {
        console.log('🔄 手动刷新表格样式');
        enhanceTables();
    };
    
    console.log('📋 后端仓入库页面增强脚本已加载');
})();
