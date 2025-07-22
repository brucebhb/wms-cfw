/**
 * 简化的性能监控脚本
 * 替代多个重复的性能优化脚本
 */

(function() {
    'use strict';

    // 性能监控器
    class SimplePerformanceMonitor {
        constructor() {
            this.startTime = performance.now();
            this.isLoading = false;
            this.init();
        }

        init() {
            this.setupLoadingIndicators();
            this.setupSearchOptimization();
            this.monitorPagePerformance();
        }

        // 设置加载指示器
        setupLoadingIndicators() {
            // 为表单提交添加加载状态
            document.addEventListener('submit', (e) => {
                if (e.target.tagName === 'FORM') {
                    this.showLoading();
                }
            });

            // 为链接点击添加加载状态
            document.addEventListener('click', (e) => {
                if (e.target.tagName === 'A' && !e.target.getAttribute('onclick')) {
                    const href = e.target.getAttribute('href');
                    if (href && !href.startsWith('#') && !href.startsWith('javascript:')) {
                        this.showLoading();
                    }
                }
            });
        }

        // 搜索优化
        setupSearchOptimization() {
            const searchInputs = document.querySelectorAll('input[type="text"], input[type="search"]');
            
            searchInputs.forEach(input => {
                let timeout;
                input.addEventListener('input', (e) => {
                    clearTimeout(timeout);
                    timeout = setTimeout(() => {
                        // 如果有特定的搜索函数，调用它
                        if (typeof window.performSearch === 'function') {
                            window.performSearch();
                        }
                    }, 300);
                });
            });
        }

        // 显示加载状态
        showLoading() {
            if (this.isLoading) return;
            
            this.isLoading = true;
            
            // 创建简单的加载指示器
            const loader = document.createElement('div');
            loader.id = 'simple-loader';
            loader.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 4px;
                background: linear-gradient(90deg, #007bff, #28a745);
                z-index: 10000;
                animation: loading 1s infinite;
            `;
            
            // 添加CSS动画
            if (!document.getElementById('loading-style')) {
                const style = document.createElement('style');
                style.id = 'loading-style';
                style.textContent = `
                    @keyframes loading {
                        0% { transform: translateX(-100%); }
                        100% { transform: translateX(100%); }
                    }
                `;
                document.head.appendChild(style);
            }
            
            document.body.appendChild(loader);
            
            // 3秒后自动移除
            setTimeout(() => {
                this.hideLoading();
            }, 3000);
        }

        // 隐藏加载状态
        hideLoading() {
            const loader = document.getElementById('simple-loader');
            if (loader) {
                loader.remove();
            }
            this.isLoading = false;
        }

        // 监控页面性能
        monitorPagePerformance() {
            window.addEventListener('load', () => {
                const loadTime = performance.now() - this.startTime;
                
                // 如果加载时间超过2秒，显示提示
                if (loadTime > 2000) {
                    console.warn(`页面加载较慢: ${loadTime.toFixed(2)}ms`);
                }
                
                // 隐藏加载指示器
                this.hideLoading();
            });
        }

        // 优化表格显示
        optimizeTable() {
            const tables = document.querySelectorAll('table');
            tables.forEach(table => {
                // 为大表格添加虚拟滚动
                const rows = table.querySelectorAll('tbody tr');
                if (rows.length > 100) {
                    this.enableVirtualScrolling(table);
                }
            });
        }

        // 简单的虚拟滚动实现
        enableVirtualScrolling(table) {
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const rowHeight = 40; // 假设每行40px
            const visibleRows = Math.ceil(window.innerHeight / rowHeight) + 5;
            
            let startIndex = 0;
            
            const updateVisibleRows = () => {
                const scrollTop = window.pageYOffset;
                startIndex = Math.floor(scrollTop / rowHeight);
                const endIndex = Math.min(startIndex + visibleRows, rows.length);
                
                // 隐藏所有行
                rows.forEach(row => row.style.display = 'none');
                
                // 显示可见行
                for (let i = startIndex; i < endIndex; i++) {
                    if (rows[i]) {
                        rows[i].style.display = '';
                    }
                }
            };
            
            // 节流滚动事件
            let ticking = false;
            window.addEventListener('scroll', () => {
                if (!ticking) {
                    requestAnimationFrame(() => {
                        updateVisibleRows();
                        ticking = false;
                    });
                    ticking = true;
                }
            });
            
            // 初始化显示
            updateVisibleRows();
        }
    }

    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.performanceMonitor = new SimplePerformanceMonitor();
        });
    } else {
        window.performanceMonitor = new SimplePerformanceMonitor();
    }

    // 导出到全局
    window.SimplePerformanceMonitor = SimplePerformanceMonitor;

})();
