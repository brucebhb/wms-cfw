/**
 * 加载状态管理
 * 提升用户体验，减少"卡顿"感觉
 */

class LoadingManager {
    constructor() {
        this.loadingOverlay = null;
        this.init();
    }

    init() {
        // 创建全局加载遮罩
        this.createLoadingOverlay();
        
        // 监听页面加载
        this.setupPageLoading();
        
        // 监听AJAX请求
        this.setupAjaxLoading();
        
        // 监听表单提交
        this.setupFormLoading();
    }

    createLoadingOverlay() {
        this.loadingOverlay = document.createElement('div');
        this.loadingOverlay.className = 'loading-overlay';
        this.loadingOverlay.style.display = 'none';
        this.loadingOverlay.innerHTML = `
            <div class="loading-spinner"></div>
            <div class="loading-text">加载中...</div>
        `;
        document.body.appendChild(this.loadingOverlay);
    }

    show(text = '加载中...') {
        if (this.loadingOverlay) {
            this.loadingOverlay.querySelector('.loading-text').textContent = text;
            this.loadingOverlay.style.display = 'flex';
        }
    }

    hide() {
        if (this.loadingOverlay) {
            this.loadingOverlay.style.display = 'none';
        }
    }

    setupPageLoading() {
        // 页面加载时显示加载动画
        window.addEventListener('beforeunload', () => {
            this.show('页面跳转中...');
        });

        // 页面加载完成后隐藏
        window.addEventListener('load', () => {
            this.hide();
        });
    }

    setupAjaxLoading() {
        // 监听所有AJAX请求
        const originalFetch = window.fetch;
        window.fetch = (...args) => {
            this.show('数据加载中...');
            return originalFetch(...args)
                .then(response => {
                    this.hide();
                    return response;
                })
                .catch(error => {
                    this.hide();
                    throw error;
                });
        };

        // 监听jQuery AJAX（如果使用）
        if (window.jQuery) {
            $(document).ajaxStart(() => {
                this.show('数据加载中...');
            });

            $(document).ajaxStop(() => {
                this.hide();
            });
        }
    }

    setupFormLoading() {
        // 监听表单提交
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.tagName === 'FORM') {
                this.show('提交中...');
                
                // 为提交按钮添加加载状态
                const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
                if (submitBtn) {
                    submitBtn.classList.add('btn-loading');
                    submitBtn.disabled = true;
                }
            }
        });
    }

    // 表格加载状态
    showTableLoading(tableSelector) {
        const table = document.querySelector(tableSelector);
        if (table) {
            table.classList.add('table-loading');
        }
    }

    hideTableLoading(tableSelector) {
        const table = document.querySelector(tableSelector);
        if (table) {
            table.classList.remove('table-loading');
        }
    }

    // 按钮加载状态
    showButtonLoading(buttonSelector) {
        const button = document.querySelector(buttonSelector);
        if (button) {
            button.classList.add('btn-loading');
            button.disabled = true;
        }
    }

    hideButtonLoading(buttonSelector) {
        const button = document.querySelector(buttonSelector);
        if (button) {
            button.classList.remove('btn-loading');
            button.disabled = false;
        }
    }
}

// 创建全局实例
window.loadingManager = new LoadingManager();

// 提供简便方法
window.showLoading = (text) => window.loadingManager.show(text);
window.hideLoading = () => window.loadingManager.hide();
window.showTableLoading = (selector) => window.loadingManager.showTableLoading(selector);
window.hideTableLoading = (selector) => window.loadingManager.hideTableLoading(selector);
window.showButtonLoading = (selector) => window.loadingManager.showButtonLoading(selector);
window.hideButtonLoading = (selector) => window.loadingManager.hideButtonLoading(selector);

// 页面特定的加载优化
document.addEventListener('DOMContentLoaded', function() {
    // 为所有链接添加加载状态
    document.querySelectorAll('a[href]:not([href^="#"]):not([href^="javascript:"])').forEach(link => {
        link.addEventListener('click', function(e) {
            // 排除外部链接和特殊链接
            if (this.hostname === window.location.hostname) {
                showLoading('页面跳转中...');
            }
        });
    });

    // 为搜索按钮添加加载状态
    document.querySelectorAll('.search-btn, button[type="submit"]').forEach(btn => {
        btn.addEventListener('click', function() {
            if (this.form && this.form.checkValidity()) {
                showButtonLoading(`#${this.id}`);
                showLoading('搜索中...');
            }
        });
    });

    // 为数据表格添加加载优化
    const tables = document.querySelectorAll('.table');
    tables.forEach(table => {
        // 如果表格数据较多，显示加载状态
        const rows = table.querySelectorAll('tbody tr');
        if (rows.length > 20) {
            table.classList.add('table-loading');
            setTimeout(() => {
                table.classList.remove('table-loading');
            }, 500);
        }
    });

    // 优化大数据量页面的渲染
    const dataContainers = document.querySelectorAll('[data-large-content]');
    dataContainers.forEach(container => {
        container.style.opacity = '0';
        setTimeout(() => {
            container.style.transition = 'opacity 0.3s';
            container.style.opacity = '1';
        }, 100);
    });
});

// 网络状态检测
if ('navigator' in window && 'onLine' in navigator) {
    window.addEventListener('online', () => {
        console.log('网络连接已恢复');
        hideLoading();
    });

    window.addEventListener('offline', () => {
        console.log('网络连接已断开');
        showLoading('网络连接中断，请检查网络...');
    });
}

// 性能监控
if ('performance' in window) {
    window.addEventListener('load', () => {
        setTimeout(() => {
            const perfData = performance.getEntriesByType('navigation')[0];
            if (perfData && perfData.loadEventEnd - perfData.loadEventStart > 3000) {
                console.warn('页面加载较慢，建议优化');
            }
        }, 0);
    });
}
