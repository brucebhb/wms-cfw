/**
 * 列表页面性能优化工具
 * 提供加载指示器、搜索防抖、表格优化等功能
 */

class ListPerformanceOptimizer {
    constructor(options = {}) {
        this.options = {
            // 搜索防抖延迟（毫秒）
            searchDebounceDelay: 300,
            // 加载指示器选择器
            tableSelector: 'table tbody',
            // 搜索输入框选择器
            searchInputSelector: 'input[type="text"], input[type="search"]',
            // 下拉选择器
            selectSelector: 'select',
            // 表单选择器
            formSelector: 'form',
            // 分页链接选择器
            paginationSelector: '.pagination a',
            ...options
        };
        
        this.searchTimeouts = new Map();
        this.isLoading = false;
        
        this.init();
    }
    
    init() {
        this.setupSearchDebounce();
        this.setupLoadingIndicators();
        this.setupTableOptimizations();
        this.setupFormOptimizations();
    }
    
    /**
     * 设置搜索防抖
     */
    setupSearchDebounce() {
        const searchInputs = document.querySelectorAll(this.options.searchInputSelector);
        
        searchInputs.forEach(input => {
            // 跳过日期输入框和已有AJAX处理的输入框
            if (input.type === 'date' ||
                input.classList.contains('date-picker') ||
                input.classList.contains('ajax-handled')) {
                return;
            }
            
            input.addEventListener('input', (e) => {
                const inputId = e.target.id || e.target.name || 'default';
                
                // 清除之前的定时器
                if (this.searchTimeouts.has(inputId)) {
                    clearTimeout(this.searchTimeouts.get(inputId));
                }
                
                // 设置新的定时器
                const timeout = setTimeout(() => {
                    this.triggerSearch(e.target);
                }, this.options.searchDebounceDelay);
                
                this.searchTimeouts.set(inputId, timeout);
            });
        });
        
        // 下拉选择器立即触发搜索
        const selects = document.querySelectorAll(this.options.selectSelector);
        selects.forEach(select => {
            // 跳过已有AJAX处理的选择器
            if (select.classList.contains('ajax-handled')) {
                return;
            }

            select.addEventListener('change', (e) => {
                this.triggerSearch(e.target);
            });
        });
    }
    
    /**
     * 触发搜索
     */
    triggerSearch(element) {
        // 检查是否是AJAX页面（有特定的全局函数）
        if (typeof window.loadUsers === 'function') {
            // 用户管理页面 - 使用AJAX加载
            window.loadUsers(1);
            return;
        }

        if (typeof window.loadData === 'function') {
            // 其他AJAX页面 - 使用通用loadData函数
            window.loadData(1);
            return;
        }

        // 传统表单提交页面
        const form = element.closest(this.options.formSelector);
        if (form) {
            this.showLoadingIndicator();
            form.submit();
        }
    }
    
    /**
     * 设置加载指示器
     */
    setupLoadingIndicators() {
        // 为表单提交添加加载指示器
        const forms = document.querySelectorAll(this.options.formSelector);
        forms.forEach(form => {
            form.addEventListener('submit', () => {
                this.showLoadingIndicator();
            });
        });
        
        // 为分页链接添加加载指示器
        const paginationLinks = document.querySelectorAll(this.options.paginationSelector);
        paginationLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                // 如果是JavaScript处理的链接，不显示加载指示器
                if (link.getAttribute('onclick')) {
                    return;
                }
                this.showLoadingIndicator();
            });
        });
    }
    
    /**
     * 显示加载指示器
     */
    showLoadingIndicator() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        const tableBody = document.querySelector(this.options.tableSelector);
        
        if (tableBody) {
            // 计算表格列数
            const firstRow = tableBody.querySelector('tr');
            const colCount = firstRow ? firstRow.children.length : 8;
            
            // 显示加载指示器
            tableBody.innerHTML = `
                <tr>
                    <td colspan="${colCount}" class="text-center py-4">
                        <div class="d-flex align-items-center justify-content-center">
                            <div class="spinner-border spinner-border-sm text-primary me-2" role="status">
                                <span class="visually-hidden">加载中...</span>
                            </div>
                            <span class="text-muted">加载中，请稍候...</span>
                        </div>
                    </td>
                </tr>
            `;
        }
        
        // 添加页面级加载指示器
        this.showPageLoadingIndicator();
    }
    
    /**
     * 显示页面级加载指示器
     */
    showPageLoadingIndicator() {
        // 创建遮罩层
        const overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(255, 255, 255, 0.8);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(2px);
        `;
        
        overlay.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary mb-2" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <div class="text-muted">正在加载数据...</div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        // 5秒后自动移除（防止卡住）
        setTimeout(() => {
            this.hidePageLoadingIndicator();
        }, 5000);
    }
    
    /**
     * 隐藏页面级加载指示器
     */
    hidePageLoadingIndicator() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.remove();
        }
        this.isLoading = false;
    }
    
    /**
     * 设置表格优化
     */
    setupTableOptimizations() {
        const tables = document.querySelectorAll('table');
        
        tables.forEach(table => {
            // 添加表格响应式包装
            if (!table.closest('.table-responsive')) {
                const wrapper = document.createElement('div');
                wrapper.className = 'table-responsive';
                table.parentNode.insertBefore(wrapper, table);
                wrapper.appendChild(table);
            }
            
            // 优化表格渲染
            table.style.tableLayout = 'fixed';
            
            // 为长文本添加省略号
            const cells = table.querySelectorAll('td');
            cells.forEach(cell => {
                if (cell.textContent.length > 50) {
                    cell.style.overflow = 'hidden';
                    cell.style.textOverflow = 'ellipsis';
                    cell.style.whiteSpace = 'nowrap';
                    cell.title = cell.textContent;
                }
            });
        });
    }
    
    /**
     * 设置表单优化
     */
    setupFormOptimizations() {
        // 防止重复提交
        const forms = document.querySelectorAll(this.options.formSelector);
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = true;
                    setTimeout(() => {
                        submitBtn.disabled = false;
                    }, 2000);
                }
            });
        });
    }
    
    /**
     * 手动触发加载指示器
     */
    showLoading() {
        this.showLoadingIndicator();
    }
    
    /**
     * 手动隐藏加载指示器
     */
    hideLoading() {
        this.hidePageLoadingIndicator();
    }
}

// 页面加载完成后自动初始化
document.addEventListener('DOMContentLoaded', function() {
    // 检查是否是列表页面
    const isListPage = document.querySelector('table') || 
                      document.querySelector('.pagination') ||
                      document.querySelector('[class*="list"]');
    
    if (isListPage) {
        window.listOptimizer = new ListPerformanceOptimizer();
        
        // 页面加载完成后隐藏加载指示器
        window.addEventListener('load', function() {
            setTimeout(() => {
                if (window.listOptimizer) {
                    window.listOptimizer.hideLoading();
                }
            }, 100);
        });
    }
});

// 导出类供其他脚本使用
window.ListPerformanceOptimizer = ListPerformanceOptimizer;
