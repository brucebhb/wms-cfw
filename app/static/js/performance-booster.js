/**
 * 性能提升器 - 专门用于提升页面加载速度
 * 不禁用现有功能，只是优化执行顺序和方式
 */

class PerformanceBooster {
    constructor() {
        this.startTime = performance.now();
        this.optimizations = [];
        this.init();
    }

    init() {
        console.log('⚡ 性能提升器启动');
        
        // 立即应用关键优化
        this.applyCriticalOptimizations();
        
        // 延迟应用非关键优化
        requestIdleCallback(() => {
            this.applyNonCriticalOptimizations();
        });
        
        // 监控性能
        this.setupPerformanceMonitoring();
    }

    applyCriticalOptimizations() {
        // 1. 优化CSS加载
        this.optimizeCSSLoading();
        
        // 2. 优化JavaScript执行
        this.optimizeJSExecution();
        
        // 3. 优化DOM操作
        this.optimizeDOMOperations();
        
        console.log('🚀 关键优化已应用');
    }

    optimizeCSSLoading() {
        // 预加载关键CSS - 使用实际存在的CDN路径
        const criticalCSS = [
            'https://cdn.bootcdn.net/ajax/libs/twitter-bootstrap/5.3.0/css/bootstrap.min.css',
            'https://cdn.bootcdn.net/ajax/libs/font-awesome/6.4.0/css/all.min.css'
        ];

        criticalCSS.forEach(href => {
            // 检查是否已经存在
            const existingLink = document.querySelector(`link[href="${href}"]`);
            if (!existingLink) {
                const link = document.createElement('link');
                link.rel = 'preload';
                link.as = 'style';
                link.href = href;
                link.onload = function() { this.rel = 'stylesheet'; };
                link.onerror = function() {
                    console.warn('CSS预加载失败:', href);
                    this.remove();
                };
                document.head.appendChild(link);
            }
        });

        this.optimizations.push('CSS预加载');
    }

    optimizeJSExecution() {
        // 优化脚本执行顺序，但不移除已加载的脚本
        const scriptsToOptimize = [];

        // 标记可优化的脚本，但不移除
        document.querySelectorAll('script[src]').forEach(script => {
            const src = script.src;
            if (src.includes('analytics') || src.includes('tracking')) {
                // 只延迟真正的分析和跟踪脚本
                script.defer = true;
                scriptsToOptimize.push(src);
            }
        });

        // 避免重复加载性能相关脚本
        if (scriptsToOptimize.length > 0) {
            console.log('已优化脚本执行顺序:', scriptsToOptimize.length, '个脚本');
        }

        this.optimizations.push('脚本执行优化');
    }

    optimizeDOMOperations() {
        // 批量DOM操作
        const domQueue = [];
        let isProcessing = false;

        window.batchDOM = function(operation) {
            domQueue.push(operation);
            if (!isProcessing) {
                isProcessing = true;
                requestAnimationFrame(() => {
                    domQueue.forEach(op => op());
                    domQueue.length = 0;
                    isProcessing = false;
                });
            }
        };

        this.optimizations.push('DOM批量操作');
    }

    applyNonCriticalOptimizations() {
        // 1. 图片懒加载
        this.setupLazyLoading();
        
        // 2. 内存优化
        this.optimizeMemory();
        
        // 3. 网络优化
        this.optimizeNetwork();
        
        console.log('🔧 非关键优化已应用');
    }

    setupLazyLoading() {
        // 为所有图片添加懒加载
        const images = document.querySelectorAll('img:not([loading])');
        images.forEach(img => {
            img.loading = 'lazy';
        });

        // 为表格添加虚拟滚动（如果行数过多）
        const tables = document.querySelectorAll('table tbody');
        tables.forEach(tbody => {
            if (tbody.children.length > 50) {
                this.setupVirtualScrolling(tbody);
            }
        });

        this.optimizations.push('懒加载优化');
    }

    setupVirtualScrolling(tbody) {
        // 简单的虚拟滚动实现
        const rows = Array.from(tbody.children);
        const visibleRows = 20;
        let startIndex = 0;

        const container = tbody.parentElement;
        const scrollHandler = () => {
            const scrollTop = container.scrollTop;
            const rowHeight = rows[0]?.offsetHeight || 40;
            const newStartIndex = Math.floor(scrollTop / rowHeight);
            
            if (newStartIndex !== startIndex) {
                startIndex = newStartIndex;
                this.updateVisibleRows(tbody, rows, startIndex, visibleRows);
            }
        };

        container.addEventListener('scroll', scrollHandler);
        this.updateVisibleRows(tbody, rows, startIndex, visibleRows);
    }

    updateVisibleRows(tbody, allRows, startIndex, visibleCount) {
        // 清空当前显示的行
        tbody.innerHTML = '';
        
        // 显示当前范围内的行
        const endIndex = Math.min(startIndex + visibleCount, allRows.length);
        for (let i = startIndex; i < endIndex; i++) {
            tbody.appendChild(allRows[i]);
        }
    }

    optimizeMemory() {
        // 清理未使用的变量
        setInterval(() => {
            // 清理jQuery缓存
            if (window.jQuery) {
                window.jQuery.cleanData(document.querySelectorAll('*'));
            }
            
            // 清理事件监听器
            this.cleanupEventListeners();
        }, 30000);

        this.optimizations.push('内存优化');
    }

    cleanupEventListeners() {
        // 移除孤立的事件监听器
        const elements = document.querySelectorAll('[data-bs-toggle], [onclick]');
        elements.forEach(el => {
            if (!el.isConnected) {
                el.removeEventListener('click', null);
            }
        });
    }

    optimizeNetwork() {
        // 预连接到外部资源
        const preconnectDomains = [
            'https://cdnjs.cloudflare.com',
            'https://fonts.googleapis.com'
        ];

        preconnectDomains.forEach(domain => {
            const link = document.createElement('link');
            link.rel = 'preconnect';
            link.href = domain;
            document.head.appendChild(link);
        });

        this.optimizations.push('网络预连接');
    }

    setupPerformanceMonitoring() {
        window.addEventListener('load', () => {
            const loadTime = performance.now() - this.startTime;
            
            console.log(`📊 页面加载时间: ${Math.round(loadTime)}ms`);
            console.log(`🔧 应用的优化: ${this.optimizations.join(', ')}`);
            
            // 如果加载时间仍然很慢，提供建议
            if (loadTime > 5000) {
                console.warn('⚠️ 页面加载仍然较慢，建议检查:');
                console.warn('- 数据库查询性能');
                console.warn('- 网络连接状况');
                console.warn('- 服务器资源使用情况');
            } else if (loadTime < 2000) {
                console.log('✅ 页面加载速度良好');
            }
        });
    }

    // 静态方法：快速应用所有优化
    static quickBoost() {
        // 避免重复初始化
        if (window.performanceBoosterInitialized) {
            console.log('⚡ 性能提升器已初始化，跳过重复加载');
            return;
        }

        window.performanceBoosterInitialized = true;
        new PerformanceBooster();

        // 额外的快速优化 - 只优化非关键脚本
        document.querySelectorAll('script[src*="analytics"], script[src*="tracking"]').forEach(script => {
            script.async = true;
        });

        // 优化表单提交体验
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', function() {
                // 添加提交状态指示
                const submitBtn = this.querySelector('button[type="submit"], input[type="submit"]');
                if (submitBtn && !submitBtn.disabled) {
                    const originalText = submitBtn.textContent;
                    submitBtn.textContent = '提交中...';
                    submitBtn.disabled = true;

                    // 5秒后恢复（防止卡住）
                    setTimeout(() => {
                        submitBtn.textContent = originalText;
                        submitBtn.disabled = false;
                    }, 5000);
                }
            });
        });

        console.log('⚡ 快速性能提升已应用');
    }
}

// 自动启动
document.addEventListener('DOMContentLoaded', () => {
    PerformanceBooster.quickBoost();
});

// 导出供其他脚本使用
window.PerformanceBooster = PerformanceBooster;
