/**
 * 自动性能检查和修复系统
 * 定期检查页面性能问题并自动应用修复措施
 */

class AutoPerformanceFixer {
    constructor() {
        this.isEnabled = true;
        this.checkInterval = 60000; // 60秒检查一次（减少频率）
        this.fixHistory = [];
        this.performanceData = {
            loadTimes: [],
            resourceErrors: [],
            memoryUsage: [],
            lastCheck: null
        };

        // 针对您的系统优化的性能阈值
        this.thresholds = {
            loadTime: 3000,      // 3秒（更严格）
            resourceTimeout: 2000, // 2秒
            memoryLimit: 80,     // 80MB（更严格）
            errorRate: 0.05,     // 5%错误率
            domElements: 2000,   // DOM元素数量
            scriptCount: 15      // 脚本数量
        };

        // 自动修复策略（安全模式）
        this.autoFixStrategies = {
            aggressiveCleanup: false,   // 禁用激进清理
            preemptiveOptimization: true, // 保留预防性优化
            realTimeMonitoring: false,  // 禁用实时监控
            adaptiveThresholds: true    // 保留自适应阈值
        };

        this.init();
    }
    
    init() {
        console.log('🔧 自动性能修复系统启动中...');

        // 立即应用预防性优化
        this.applyPreventiveOptimizations();

        // 等待页面完全加载后开始监控
        if (document.readyState === 'complete') {
            this.startMonitoring();
        } else {
            window.addEventListener('load', () => {
                setTimeout(() => this.startMonitoring(), 1000); // 更快启动
            });
        }

        // 监听页面可见性变化
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible' && this.isEnabled) {
                this.performQuickCheck();
            }
        });

        // 监听路由变化（针对SPA）
        window.addEventListener('popstate', () => {
            setTimeout(() => this.performQuickCheck(), 500);
        });

        // 暂时禁用DOM监控以避免干扰菜单
        // this.observeDOM();
    }
    
    startMonitoring() {
        console.log('🔍 开始性能监控和自动修复...');
        
        // 立即执行一次检查
        this.performFullCheck();
        
        // 定期检查 - 添加清理机制
        this.checkTimer = setInterval(() => {
            if (this.isEnabled && document.visibilityState === 'visible') {
                this.performFullCheck();
            }
        }, this.checkInterval);

        // 页面卸载时清理定时器
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
        
        // 监控资源加载错误
        this.monitorResourceErrors();
        
        // 监控内存使用
        this.monitorMemoryUsage();
    }
    
    async performFullCheck() {
        const checkTime = Date.now();
        console.log('🔍 执行完整性能检查...');
        
        try {
            // 1. 检查页面加载时间
            await this.checkLoadTime();
            
            // 2. 检查资源加载状态
            await this.checkResourceHealth();
            
            // 3. 检查DOM性能
            await this.checkDOMPerformance();
            
            // 4. 检查内存使用
            await this.checkMemoryUsage();
            
            // 5. 检查网络状态
            await this.checkNetworkStatus();
            
            // 6. 应用自动修复
            await this.applyAutoFixes();
            
            this.performanceData.lastCheck = checkTime;
            console.log('✅ 性能检查完成');
            
        } catch (error) {
            console.error('❌ 性能检查失败:', error);
        }
    }
    
    async performQuickCheck() {
        console.log('⚡ 执行快速性能检查...');
        
        // 快速检查关键指标
        const issues = [];
        
        // 检查页面响应性
        const startTime = performance.now();
        await new Promise(resolve => setTimeout(resolve, 0));
        const responseTime = performance.now() - startTime;
        
        if (responseTime > 100) {
            issues.push('页面响应缓慢');
            this.fixPageResponsiveness();
        }
        
        // 检查内存使用
        if (this.checkMemoryUsage()) {
            issues.push('内存使用过高');
            this.fixMemoryIssues();
        }
        
        if (issues.length > 0) {
            console.log('🔧 发现问题并自动修复:', issues);
        }
    }
    
    async checkLoadTime() {
        const navigation = performance.getEntriesByType('navigation')[0];
        if (navigation) {
            const loadTime = navigation.loadEventEnd - navigation.fetchStart;
            this.performanceData.loadTimes.push(loadTime);
            
            if (loadTime > this.thresholds.loadTime) {
                console.warn(`⚠️ 页面加载时间过长: ${(loadTime/1000).toFixed(2)}s`);
                this.fixSlowLoading();
                return false;
            }
        }
        return true;
    }
    
    async checkResourceHealth() {
        const resources = performance.getEntriesByType('resource');
        const slowResources = resources.filter(r => r.duration > this.thresholds.resourceTimeout);
        
        if (slowResources.length > 0) {
            console.warn('⚠️ 发现慢速资源:', slowResources.map(r => r.name));
            this.fixSlowResources(slowResources);
        }
        
        return slowResources.length === 0;
    }
    
    async checkDOMPerformance() {
        const domElements = document.querySelectorAll('*').length;
        const heavyElements = document.querySelectorAll('img, video, iframe').length;
        
        if (domElements > 3000) {
            console.warn('⚠️ DOM元素过多:', domElements);
            this.fixDOMComplexity();
        }
        
        if (heavyElements > 50) {
            console.warn('⚠️ 重型元素过多:', heavyElements);
            this.fixHeavyElements();
        }
    }
    
    checkMemoryUsage() {
        if ('memory' in performance) {
            const memory = performance.memory;
            const usedMB = memory.usedJSHeapSize / 1024 / 1024;
            
            this.performanceData.memoryUsage.push(usedMB);
            
            if (usedMB > this.thresholds.memoryLimit) {
                console.warn(`⚠️ 内存使用过高: ${usedMB.toFixed(2)}MB`);
                return true;
            }
        }
        return false;
    }
    
    async checkNetworkStatus() {
        if ('connection' in navigator) {
            const connection = navigator.connection;
            if (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g') {
                console.warn('⚠️ 网络连接较慢');
                this.fixSlowNetwork();
            }
        }
    }
    
    monitorResourceErrors() {
        // 监控图片加载错误
        document.addEventListener('error', (e) => {
            if (e.target.tagName === 'IMG') {
                console.warn('❌ 图片加载失败:', e.target.src);
                this.fixImageError(e.target);
            }
        }, true);
        
        // 监控脚本加载错误
        window.addEventListener('error', (e) => {
            console.error('❌ 脚本错误:', e.message);
            this.performanceData.resourceErrors.push({
                type: 'script',
                message: e.message,
                time: Date.now()
            });
        });
    }
    
    monitorMemoryUsage() {
        if ('memory' in performance) {
            setInterval(() => {
                const memory = performance.memory;
                const usedMB = memory.usedJSHeapSize / 1024 / 1024;
                
                if (usedMB > this.thresholds.memoryLimit) {
                    this.fixMemoryIssues();
                }
            }, 60000); // 每分钟检查一次
        }
    }
    
    // ==================== 自动修复方法 ====================
    
    async applyAutoFixes() {
        // 清理无用的事件监听器
        this.cleanupEventListeners();
        
        // 优化CSS
        this.optimizeCSS();
        
        // 清理DOM
        this.cleanupDOM();
        
        // 优化图片
        this.optimizeImages();
    }
    
    fixSlowLoading() {
        console.log('🔧 修复慢速加载...');
        
        // 移除不必要的CSS
        const unusedStyles = document.querySelectorAll('style:empty, link[rel="stylesheet"]:not([href*="bootstrap"]):not([href*="fontawesome"])');
        unusedStyles.forEach(style => {
            if (style.sheet && style.sheet.cssRules.length === 0) {
                style.remove();
            }
        });
        
        // 延迟加载非关键脚本
        const scripts = document.querySelectorAll('script[src]:not([async]):not([defer])');
        scripts.forEach(script => {
            if (!script.src.includes('jquery') && !script.src.includes('bootstrap')) {
                script.defer = true;
            }
        });
        
        this.addFixToHistory('修复慢速加载');
    }
    
    fixSlowResources(resources) {
        console.log('🔧 修复慢速资源...');
        
        resources.forEach(resource => {
            // 对于图片资源，添加懒加载
            if (resource.name.match(/\.(jpg|jpeg|png|gif|webp)$/i)) {
                const imgs = document.querySelectorAll(`img[src="${resource.name}"]`);
                imgs.forEach(img => {
                    if (!img.loading) {
                        img.loading = 'lazy';
                    }
                });
            }
        });
        
        this.addFixToHistory('修复慢速资源');
    }
    
    fixPageResponsiveness() {
        console.log('🔧 修复页面响应性...');
        
        // 使用requestIdleCallback优化任务
        if ('requestIdleCallback' in window) {
            const heavyTasks = [];
            
            // 将重型操作推迟到空闲时间
            requestIdleCallback(() => {
                heavyTasks.forEach(task => task());
            });
        }
        
        this.addFixToHistory('修复页面响应性');
    }
    
    fixMemoryIssues() {
        console.log('🔧 修复内存问题...');
        
        // 清理缓存
        if ('caches' in window) {
            caches.keys().then(names => {
                names.forEach(name => {
                    if (name.includes('old') || name.includes('temp')) {
                        caches.delete(name);
                    }
                });
            });
        }
        
        // 清理大型数据结构
        this.cleanupLargeObjects();
        
        // 强制垃圾回收（如果可用）
        if (window.gc) {
            window.gc();
        }
        
        this.addFixToHistory('修复内存问题');
    }
    
    fixDOMComplexity() {
        console.log('🔧 优化DOM复杂度...');
        
        // 移除隐藏的元素
        const hiddenElements = document.querySelectorAll('[style*="display: none"], .d-none:not(.modal)');
        hiddenElements.forEach(el => {
            if (!el.closest('.modal') && !el.dataset.keep) {
                el.remove();
            }
        });
        
        this.addFixToHistory('优化DOM复杂度');
    }
    
    fixHeavyElements() {
        console.log('🔧 优化重型元素...');
        
        // 为图片添加懒加载
        const images = document.querySelectorAll('img:not([loading])');
        images.forEach(img => {
            img.loading = 'lazy';
        });
        
        // 为iframe添加懒加载
        const iframes = document.querySelectorAll('iframe:not([loading])');
        iframes.forEach(iframe => {
            iframe.loading = 'lazy';
        });
        
        this.addFixToHistory('优化重型元素');
    }
    
    fixSlowNetwork() {
        console.log('🔧 优化网络性能...');
        
        // 压缩图片质量
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            if (img.src && !img.src.includes('data:')) {
                // 添加图片压缩参数（如果支持）
                if (img.src.includes('?')) {
                    img.src += '&quality=80&format=webp';
                } else {
                    img.src += '?quality=80&format=webp';
                }
            }
        });
        
        this.addFixToHistory('优化网络性能');
    }
    
    fixImageError(img) {
        console.log('🔧 修复图片错误...');
        
        // 使用占位图片
        img.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2VlZSIvPjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1zaXplPSIxMiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iIGZpbGw9IiM5OTkiPuWbvueJh+WKoOi9veWksei0pTwvdGV4dD48L3N2Zz4=';
        img.alt = '图片加载失败';
        
        this.addFixToHistory('修复图片错误');
    }

    // ==================== 新增的专门优化方法 ====================

    applyPreventiveOptimizations() {
        console.log('🚀 应用预防性优化...');

        // 1. 立即优化CSS加载
        this.optimizeCSSLoading();

        // 2. 优化脚本加载
        this.optimizeScriptLoading();

        // 3. 预加载关键资源
        this.preloadCriticalResources();

        // 4. 设置资源提示
        this.setupResourceHints();

        // 5. 优化字体加载
        this.optimizeFontLoading();

        this.addFixToHistory('应用预防性优化');
    }

    observeDOM() {
        if (!window.MutationObserver) return;

        const observer = new MutationObserver((mutations) => {
            let significantChanges = 0;

            mutations.forEach(mutation => {
                if (mutation.type === 'childList') {
                    significantChanges += mutation.addedNodes.length;
                }
            });

            // 如果DOM变化较大，触发优化
            if (significantChanges > 10) {
                setTimeout(() => this.performQuickCheck(), 100);
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: false
        });
    }

    optimizeCSSLoading() {
        // 为CSS添加预加载
        const criticalCSS = [
            'bootstrap.min.css',
            'fontawesome'
        ];

        const links = document.querySelectorAll('link[rel="stylesheet"]');
        links.forEach(link => {
            const href = link.href;

            // 为关键CSS添加高优先级
            if (criticalCSS.some(css => href.includes(css))) {
                link.setAttribute('importance', 'high');
            } else {
                // 非关键CSS延迟加载
                link.media = 'print';
                link.onload = function() {
                    this.media = 'all';
                };
            }
        });
    }

    optimizeScriptLoading() {
        const scripts = document.querySelectorAll('script[src]');
        const criticalScripts = ['jquery', 'bootstrap'];

        scripts.forEach(script => {
            const src = script.src;

            // 跳过已经有async/defer的脚本
            if (script.async || script.defer) return;

            // 关键脚本保持同步，其他脚本异步加载
            if (!criticalScripts.some(critical => src.includes(critical))) {
                script.defer = true;
            }
        });
    }

    preloadCriticalResources() {
        // 不预加载可能不存在的资源，避免404错误
        const criticalResources = [];

        // 只预加载确实存在的资源
        const existingLinks = document.querySelectorAll('link[rel="stylesheet"]');
        const existingScripts = document.querySelectorAll('script[src]');

        // 检查现有资源，不添加可能不存在的预加载
        console.debug('跳过资源预加载以避免404错误');

        criticalResources.forEach(resource => {
            // 检查是否已经存在
            const existing = document.querySelector(`link[href="${resource.href}"]`);
            if (!existing) {
                const link = document.createElement('link');
                link.rel = 'preload';
                link.href = resource.href;
                link.as = resource.as;
                if (resource.as === 'style') {
                    link.onload = function() {
                        this.rel = 'stylesheet';
                    };
                }
                document.head.appendChild(link);
            }
        });
    }

    setupResourceHints() {
        const hints = [
            { rel: 'dns-prefetch', href: '//cdn.bootcdn.net' },
            { rel: 'dns-prefetch', href: '//fonts.googleapis.com' },
            { rel: 'preconnect', href: 'https://cdn.jsdelivr.net' }
        ];

        hints.forEach(hint => {
            const existing = document.querySelector(`link[rel="${hint.rel}"][href="${hint.href}"]`);
            if (!existing) {
                const link = document.createElement('link');
                link.rel = hint.rel;
                link.href = hint.href;
                document.head.appendChild(link);
            }
        });
    }

    optimizeFontLoading() {
        // 为字体添加font-display: swap
        const style = document.createElement('style');
        style.textContent = `
            @font-face {
                font-display: swap;
            }
            * {
                font-display: swap;
            }
        `;
        document.head.appendChild(style);
    }

    // 增强的快速检查
    async performQuickCheck() {
        console.log('⚡ 执行增强快速检查...');

        const issues = [];
        const fixes = [];

        // 1. 检查页面响应性
        const startTime = performance.now();
        await new Promise(resolve => setTimeout(resolve, 0));
        const responseTime = performance.now() - startTime;

        if (responseTime > 50) { // 更严格的阈值
            issues.push('页面响应缓慢');
            this.fixPageResponsiveness();
            fixes.push('优化页面响应性');
        }

        // 2. 检查DOM复杂度
        const domCount = document.querySelectorAll('*').length;
        if (domCount > this.thresholds.domElements) {
            issues.push('DOM元素过多');
            this.fixDOMComplexity();
            fixes.push('简化DOM结构');
        }

        // 3. 检查脚本数量
        const scriptCount = document.querySelectorAll('script').length;
        if (scriptCount > this.thresholds.scriptCount) {
            issues.push('脚本文件过多');
            this.optimizeScripts();
            fixes.push('优化脚本加载');
        }

        // 4. 检查内存使用
        if (this.checkMemoryUsage()) {
            issues.push('内存使用过高');
            this.fixMemoryIssues();
            fixes.push('清理内存');
        }

        // 5. 检查未使用的CSS
        this.removeUnusedCSS();

        // 6. 优化图片
        this.optimizeImagesAggressively();

        if (issues.length > 0) {
            console.log('🔧 发现并修复问题:', issues);
            console.log('✅ 应用修复:', fixes);
        }
    }

    optimizeScripts() {
        // 移除重复的脚本
        const scripts = document.querySelectorAll('script[src]');
        const seenSrcs = new Set();

        scripts.forEach(script => {
            if (seenSrcs.has(script.src)) {
                script.remove();
            } else {
                seenSrcs.add(script.src);
            }
        });

        // 合并小的内联脚本
        const inlineScripts = document.querySelectorAll('script:not([src])');
        if (inlineScripts.length > 5) {
            const combinedScript = document.createElement('script');
            let combinedContent = '';

            inlineScripts.forEach(script => {
                if (script.textContent.length < 500) { // 只合并小脚本
                    combinedContent += script.textContent + '\n';
                    script.remove();
                }
            });

            if (combinedContent) {
                combinedScript.textContent = combinedContent;
                document.head.appendChild(combinedScript);
            }
        }
    }

    removeUnusedCSS() {
        const styles = document.querySelectorAll('style');
        styles.forEach(style => {
            if (style.textContent.length === 0) {
                style.remove();
            }
        });

        // 移除空的CSS规则（安全版本）
        const links = document.querySelectorAll('link[rel="stylesheet"]');
        links.forEach(link => {
            try {
                if (link.sheet && link.sheet.cssRules && link.sheet.cssRules.length === 0) {
                    link.remove();
                }
            } catch (e) {
                // 跨域CSS无法访问，跳过
                console.debug('跳过跨域CSS检查:', link.href);
            }
        });
    }

    optimizeImagesAggressively() {
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            // 添加现代化属性
            if (!img.loading) img.loading = 'lazy';
            if (!img.decoding) img.decoding = 'async';

            // 为大图片添加尺寸限制
            if (img.naturalWidth > 1920 || img.naturalHeight > 1080) {
                img.style.maxWidth = '100%';
                img.style.height = 'auto';
            }

            // 添加错误处理
            if (!img.onerror) {
                img.onerror = function() {
                    this.style.display = 'none';
                };
            }
        });
    }
    
    // ==================== 辅助方法 ====================
    
    cleanupEventListeners() {
        // 暂时禁用事件监听器清理以保护菜单功能
        console.debug('跳过事件监听器清理以保护菜单功能');
    }
    
    optimizeCSS() {
        // 移除未使用的CSS规则（简化版）
        const styles = document.querySelectorAll('style');
        styles.forEach(style => {
            if (style.textContent.length > 10000) {
                // 大型样式表可能需要优化
                console.log('发现大型样式表，建议优化');
            }
        });
    }
    
    cleanupDOM() {
        // 清理空的元素
        const emptyElements = document.querySelectorAll('div:empty, span:empty, p:empty');
        emptyElements.forEach(el => {
            if (!el.dataset.keep && el.children.length === 0) {
                el.remove();
            }
        });
    }
    
    optimizeImages() {
        // 为所有图片添加现代化属性
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            if (!img.decoding) {
                img.decoding = 'async';
            }
            if (!img.loading) {
                img.loading = 'lazy';
            }
        });
    }
    
    cleanupLargeObjects() {
        // 清理可能的大型对象
        if (window.performanceData) {
            // 只保留最近的数据
            Object.keys(window.performanceData).forEach(key => {
                if (Array.isArray(window.performanceData[key])) {
                    window.performanceData[key] = window.performanceData[key].slice(-100);
                }
            });
        }
    }
    
    addFixToHistory(fix) {
        this.fixHistory.push({
            fix: fix,
            time: new Date().toISOString(),
            performance: this.getCurrentPerformance()
        });
        
        // 只保留最近50条记录
        if (this.fixHistory.length > 50) {
            this.fixHistory = this.fixHistory.slice(-50);
        }
        
        console.log(`✅ 已应用修复: ${fix}`);
    }
    
    getCurrentPerformance() {
        const navigation = performance.getEntriesByType('navigation')[0];
        return navigation ? {
            loadTime: navigation.loadEventEnd - navigation.fetchStart,
            domContentLoaded: navigation.domContentLoadedEventEnd - navigation.fetchStart
        } : null;
    }
    
    // ==================== 公共API ====================
    
    getStatus() {
        return {
            isEnabled: this.isEnabled,
            lastCheck: this.performanceData.lastCheck,
            fixHistory: this.fixHistory.slice(-10),
            currentPerformance: this.getCurrentPerformance()
        };
    }
    
    enable() {
        this.isEnabled = true;
        console.log('✅ 自动性能修复已启用');
    }
    
    disable() {
        this.isEnabled = false;
        this.cleanup();
        console.log('⏸️ 自动性能修复已禁用');
    }

    // 清理资源
    cleanup() {
        if (this.checkTimer) {
            clearInterval(this.checkTimer);
            this.checkTimer = null;
        }
        if (this.memoryTimer) {
            clearInterval(this.memoryTimer);
            this.memoryTimer = null;
        }
        console.log('🧹 性能修复器资源已清理');
    }
    
    forceCheck() {
        console.log('🔧 强制执行性能检查...');
        this.performFullCheck();
    }
}

// 全局初始化
window.AutoPerformanceFixer = AutoPerformanceFixer;

// 自动启动（延迟启动以避免影响初始加载）
setTimeout(() => {
    if (!window.autoPerformanceFixer) {
        window.autoPerformanceFixer = new AutoPerformanceFixer();
        console.log('🚀 自动性能修复系统已启动');
    }
}, 3000);

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AutoPerformanceFixer;
}
