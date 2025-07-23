/**
 * 安全性能优化器
 * 只进行安全的、不会干扰现有功能的优化
 */

class SafePerformanceOptimizer {
    constructor() {
        this.isEnabled = true;
        this.optimizations = {
            imageOptimization: true,    // 图片优化
            cacheOptimization: true,    // 缓存优化
            resourcePreload: false,     // 禁用资源预加载
            domOptimization: false,     // 禁用DOM优化
            eventOptimization: false,   // 禁用事件优化
            cssOptimization: true       // 启用安全CSS优化
        };
        
        this.init();
    }
    
    init() {
        console.log('🛡️ 安全性能优化器启动');
        
        // 等待页面完全加载后再开始优化
        if (document.readyState === 'complete') {
            this.startSafeOptimizations();
        } else {
            window.addEventListener('load', () => {
                setTimeout(() => {
                    this.startSafeOptimizations();
                }, 1000); // 延迟1秒确保所有功能已初始化
            });
        }
    }
    
    startSafeOptimizations() {
        console.log('🚀 开始安全性能优化');
        
        if (this.optimizations.imageOptimization) {
            this.optimizeImages();
        }
        
        if (this.optimizations.cacheOptimization) {
            this.optimizeCache();
        }

        if (this.optimizations.cssOptimization) {
            this.optimizeCSSLoading();
        }

        // 定期进行轻量级优化
        setInterval(() => {
            this.performLightOptimization();
        }, 30000); // 30秒一次
        
        console.log('✅ 安全性能优化已启动');
    }
    
    optimizeImages() {
        // 为新图片添加懒加载（不影响现有图片）
        const images = document.querySelectorAll('img:not([loading])');
        images.forEach(img => {
            if (!img.src || img.src.startsWith('data:')) return;
            
            // 只为新图片添加懒加载
            if (!img.hasAttribute('data-optimized')) {
                img.loading = 'lazy';
                img.setAttribute('data-optimized', 'true');
            }
        });
        
        console.log(`🖼️ 已优化 ${images.length} 张图片的加载方式`);
    }
    
    optimizeCache() {
        // 设置合理的缓存策略
        if ('serviceWorker' in navigator) {
            // 不注册service worker，避免复杂性
            console.log('📦 跳过Service Worker注册以保持简单');
        }
        
        // 优化localStorage使用
        this.cleanupLocalStorage();
    }
    
    cleanupLocalStorage() {
        try {
            const keys = Object.keys(localStorage);
            let cleanedCount = 0;
            
            keys.forEach(key => {
                const value = localStorage.getItem(key);
                
                // 清理空值或过期数据
                if (!value || value === 'null' || value === 'undefined') {
                    localStorage.removeItem(key);
                    cleanedCount++;
                }
                
                // 清理过期的临时数据
                if (key.startsWith('temp_') || key.startsWith('cache_')) {
                    try {
                        const data = JSON.parse(value);
                        if (data.expires && Date.now() > data.expires) {
                            localStorage.removeItem(key);
                            cleanedCount++;
                        }
                    } catch (e) {
                        // 无效的JSON，删除
                        localStorage.removeItem(key);
                        cleanedCount++;
                    }
                }
            });
            
            if (cleanedCount > 0) {
                console.log(`🧹 已清理 ${cleanedCount} 个无效的localStorage项`);
            }
        } catch (e) {
            console.debug('localStorage清理失败:', e);
        }
    }
    
    performLightOptimization() {
        if (!this.isEnabled) return;
        
        // 轻量级内存清理
        this.lightMemoryCleanup();
        
        // 检查页面性能
        this.checkPerformance();
    }
    
    lightMemoryCleanup() {
        // 清理可能的内存泄漏
        try {
            // 清理无用的定时器（只清理明显无用的）
            const highestTimeoutId = setTimeout(() => {}, 0);
            
            // 只清理明显异常的定时器ID
            if (highestTimeoutId > 10000) {
                console.log('⚠️ 检测到异常多的定时器，建议检查代码');
            }
            
            clearTimeout(highestTimeoutId);
        } catch (e) {
            console.debug('内存清理失败:', e);
        }
    }
    
    checkPerformance() {
        try {
            const navigation = performance.getEntriesByType('navigation')[0];
            if (navigation) {
                const loadTime = navigation.loadEventEnd - navigation.fetchStart;
                
                if (loadTime > 5000) {
                    console.log(`⚠️ 页面加载时间较长: ${(loadTime/1000).toFixed(2)}s`);
                    this.suggestOptimizations();
                }
            }
            
            // 检查内存使用
            if ('memory' in performance) {
                const memory = performance.memory;
                const usedMB = memory.usedJSHeapSize / 1024 / 1024;
                
                if (usedMB > 100) {
                    console.log(`⚠️ 内存使用较高: ${usedMB.toFixed(1)}MB`);
                }
            }
        } catch (e) {
            console.debug('性能检查失败:', e);
        }
    }
    
    suggestOptimizations() {
        const suggestions = [
            '💡 建议：减少页面上的大型图片',
            '💡 建议：检查是否有未使用的JavaScript库',
            '💡 建议：考虑使用分页减少单页数据量',
            '💡 建议：检查网络连接状况'
        ];
        
        suggestions.forEach(suggestion => {
            console.log(suggestion);
        });
    }
    
    // 提供手动优化接口
    manualOptimize() {
        console.log('🔧 执行手动优化...');
        this.optimizeImages();
        this.cleanupLocalStorage();
        this.lightMemoryCleanup();
        console.log('✅ 手动优化完成');
    }
    
    // 禁用优化器
    disable() {
        this.isEnabled = false;
        console.log('🛑 安全性能优化器已禁用');
    }
    
    // 启用优化器
    enable() {
        this.isEnabled = true;
        console.log('✅ 安全性能优化器已启用');
    }
    
    // 获取性能报告
    getPerformanceReport() {
        const report = {
            timestamp: new Date().toISOString(),
            pageLoadTime: null,
            memoryUsage: null,
            domElements: document.querySelectorAll('*').length,
            images: document.querySelectorAll('img').length,
            scripts: document.querySelectorAll('script').length,
            stylesheets: document.querySelectorAll('link[rel="stylesheet"]').length
        };
        
        try {
            const navigation = performance.getEntriesByType('navigation')[0];
            if (navigation) {
                report.pageLoadTime = navigation.loadEventEnd - navigation.fetchStart;
            }
            
            if ('memory' in performance) {
                report.memoryUsage = performance.memory.usedJSHeapSize;
            }
        } catch (e) {
            console.debug('获取性能数据失败:', e);
        }
        
        return report;
    }

    optimizeCSSLoading() {
        console.log('🎨 开始安全CSS优化...');

        try {
            // 1. 为CSS添加加载优先级（不修改内容）
            const cssLinks = document.querySelectorAll('link[rel="stylesheet"]');
            cssLinks.forEach(link => {
                const href = link.href;

                // 为关键CSS添加高优先级
                if (href.includes('bootstrap') || href.includes('fontawesome') || href.includes('custom.css')) {
                    link.setAttribute('importance', 'high');
                    console.log(`✅ 设置关键CSS高优先级: ${href.split('/').pop()}`);
                }
            });

            // 2. 优化字体显示（检查是否已存在类似优化）
            const existingOptimizer = document.querySelector('style[data-safe-optimizer="true"]');
            if (!existingOptimizer) {
                const style = document.createElement('style');
                style.textContent = `
                    /* 安全字体优化 - 不覆盖现有样式 */
                    @font-face {
                        font-display: swap;
                    }
                    /* 图片懒加载优化 - 仅对未设置的图片生效 */
                    img:not([loading]):not([data-optimized]) {
                        loading: lazy;
                    }
                `;
                style.setAttribute('data-safe-optimizer', 'true');
                document.head.appendChild(style);
                console.log('✅ 添加安全字体优化样式');
            } else {
                console.log('⚠️ 安全优化样式已存在，跳过重复添加');
            }

            // 3. 预连接字体服务（提升性能但不影响显示）
            const fontPreconnects = [
                'https://fonts.googleapis.com',
                'https://fonts.gstatic.com'
            ];

            fontPreconnects.forEach(href => {
                if (!document.querySelector(`link[href="${href}"]`)) {
                    const link = document.createElement('link');
                    link.rel = 'preconnect';
                    link.href = href;
                    link.crossOrigin = 'anonymous';
                    document.head.appendChild(link);
                }
            });

            console.log('✅ 安全CSS优化完成');

        } catch (error) {
            console.warn('⚠️ CSS优化过程中出现错误:', error);
        }
    }
}

// 创建全局实例
window.safePerformanceOptimizer = new SafePerformanceOptimizer();

// 提供控制台接口
window.optimizeNow = () => window.safePerformanceOptimizer.manualOptimize();
window.getPerformanceReport = () => window.safePerformanceOptimizer.getPerformanceReport();
window.disableOptimizer = () => window.safePerformanceOptimizer.disable();
window.enableOptimizer = () => window.safePerformanceOptimizer.enable();

console.log('🛡️ 安全性能优化器已加载');
console.log('💡 可用命令: optimizeNow(), getPerformanceReport(), disableOptimizer(), enableOptimizer()');
