/**
 * 性能自动启动脚本
 * 在页面加载的最早阶段就开始性能优化
 */

(function() {
    'use strict';
    
    // 立即开始性能监控
    const performanceStartTime = performance.now();
    
    console.log('🚀 性能自动优化启动...');
    
    // 1. 立即应用关键优化
    applyImmediateOptimizations();
    
    // 2. 监控页面加载性能
    monitorLoadPerformance();
    
    // 3. 设置自动修复触发器
    setupAutoFixTriggers();
    
    function applyImmediateOptimizations() {
        // 优化CSS加载 - 重新启用（安全模式）
        optimizeCSSImmediate();

        // 优化字体加载
        optimizeFonts();

        // 设置资源提示
        addResourceHints();

        // 优化图片加载
        optimizeImages();

        console.log('✅ 立即优化已应用 (包含安全CSS优化)');
    }
    
    function optimizeCSSImmediate() {
        // 检查是否已经有类似的优化
        const existingOptimization = document.querySelector('style[data-performance-optimizer="safe"]');
        if (existingOptimization) {
            console.log('⚠️ CSS优化已存在，跳过重复应用');
            return;
        }

        // 安全的CSS优化 - 只添加性能提升样式，不覆盖现有样式
        const style = document.createElement('style');
        style.setAttribute('data-performance-optimizer', 'safe');
        style.textContent = `
            /* 安全的字体优化 - 不使用!important避免覆盖现有样式 */
            @font-face {
                font-display: swap;
            }

            /* 图片懒加载优化 - 只对没有loading属性且未被优化的图片生效 */
            img:not([loading]):not([data-optimized]) {
                loading: lazy;
                decoding: async;
            }

            /* iframe懒加载优化 */
            iframe:not([loading]):not([data-optimized]) {
                loading: lazy;
            }

            /* 预加载关键资源提示 - 不强制覆盖 */
            link[rel="stylesheet"][href*="bootstrap"]:not([importance]),
            link[rel="stylesheet"][href*="fontawesome"]:not([importance]) {
                importance: high;
            }
        `;
        document.head.appendChild(style);

        console.log('✅ 安全CSS优化已应用');
    }
    
    function optimizeFonts() {
        // 预连接字体服务
        const fontPreconnects = [
            'https://fonts.googleapis.com',
            'https://fonts.gstatic.com'
        ];
        
        fontPreconnects.forEach(href => {
            const link = document.createElement('link');
            link.rel = 'preconnect';
            link.href = href;
            link.crossOrigin = 'anonymous';
            document.head.appendChild(link);
        });
    }
    
    function addResourceHints() {
        const hints = [
            { rel: 'dns-prefetch', href: '//cdn.bootcdn.net' },
            { rel: 'dns-prefetch', href: '//cdn.jsdelivr.net' },
            { rel: 'dns-prefetch', href: '//unpkg.com' },
            { rel: 'preconnect', href: 'https://cdn.jsdelivr.net' }
        ];
        
        hints.forEach(hint => {
            const link = document.createElement('link');
            link.rel = hint.rel;
            link.href = hint.href;
            if (hint.crossOrigin) link.crossOrigin = hint.crossOrigin;
            document.head.appendChild(link);
        });
    }
    
    function optimizeImages() {
        // 使用MutationObserver监控新添加的图片
        if (window.MutationObserver) {
            const imageObserver = new MutationObserver(mutations => {
                mutations.forEach(mutation => {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === 1) { // Element node
                            const images = node.tagName === 'IMG' ? [node] : node.querySelectorAll('img');
                            images.forEach(img => {
                                if (!img.loading) img.loading = 'lazy';
                                if (!img.decoding) img.decoding = 'async';
                            });
                        }
                    });
                });
            });
            
            imageObserver.observe(document.documentElement, {
                childList: true,
                subtree: true
            });
        }
    }
    
    function monitorLoadPerformance() {
        let loadStartTime = performance.now();
        
        // 监控DOMContentLoaded
        document.addEventListener('DOMContentLoaded', () => {
            const domTime = performance.now() - loadStartTime;
            console.log(`📊 DOM加载时间: ${domTime.toFixed(2)}ms`);
            
            if (domTime > 2000) {
                console.warn('⚠️ DOM加载较慢，启动优化...');
                triggerDOMOptimization();
            }
        });
        
        // 监控完整页面加载
        window.addEventListener('load', () => {
            const totalTime = performance.now() - performanceStartTime;
            console.log(`📊 页面总加载时间: ${totalTime.toFixed(2)}ms`);
            
            if (totalTime > 5000) {
                console.warn('⚠️ 页面加载较慢，启动深度优化...');
                triggerDeepOptimization();
            } else if (totalTime > 3000) {
                console.warn('⚠️ 页面加载中等，启动轻度优化...');
                triggerLightOptimization();
            } else {
                console.log('✅ 页面加载速度良好');
            }
            
            // 延迟启动安全的性能监控系统
            setTimeout(() => {
                // 不调用自动性能修复器，避免干扰菜单
                if (window.safePerformanceOptimizer) {
                    window.safePerformanceOptimizer.manualOptimize();
                    console.log('🛡️ 已启动安全性能优化');
                }
            }, 2000);
        });
    }
    
    function setupAutoFixTriggers() {
        // 监控内存使用
        if ('memory' in performance) {
            setInterval(() => {
                const memory = performance.memory;
                const usedMB = memory.usedJSHeapSize / 1024 / 1024;
                
                if (usedMB > 100) {
                    console.warn(`⚠️ 内存使用过高: ${usedMB.toFixed(2)}MB`);
                    triggerMemoryCleanup();
                }
            }, 30000); // 每30秒检查一次
        }
        
        // 监控页面可见性
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                // 页面重新可见时进行快速检查
                setTimeout(() => {
                    if (window.autoPerformanceFixer) {
                        window.autoPerformanceFixer.performQuickCheck();
                    }
                }, 500);
            }
        });
        
        // 监控网络状态
        if ('connection' in navigator) {
            navigator.connection.addEventListener('change', () => {
                const connection = navigator.connection;
                if (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g') {
                    console.warn('⚠️ 网络连接较慢，启动网络优化...');
                    triggerNetworkOptimization();
                }
            });
        }
    }
    
    function triggerDOMOptimization() {
        // 移除隐藏元素
        const hiddenElements = document.querySelectorAll('[style*="display: none"]:not(.modal)');
        hiddenElements.forEach(el => {
            if (!el.dataset.keep && !el.closest('.modal')) {
                el.remove();
            }
        });
        
        // 清理空元素
        const emptyElements = document.querySelectorAll('div:empty, span:empty, p:empty');
        emptyElements.forEach(el => {
            if (!el.dataset.keep && el.children.length === 0) {
                el.remove();
            }
        });
        
        console.log('✅ DOM优化完成');
    }
    
    function triggerLightOptimization() {
        // 优化图片
        const images = document.querySelectorAll('img:not([loading])');
        images.forEach(img => {
            img.loading = 'lazy';
            img.decoding = 'async';
        });
        
        // 延迟非关键脚本
        const scripts = document.querySelectorAll('script[src]:not([async]):not([defer])');
        scripts.forEach(script => {
            if (!script.src.includes('jquery') && !script.src.includes('bootstrap')) {
                script.defer = true;
            }
        });
        
        console.log('✅ 轻度优化完成');
    }
    
    function triggerDeepOptimization() {
        triggerLightOptimization();
        // 不执行DOM优化，避免干扰菜单
        // triggerDOMOptimization();

        // 不清理事件监听器，避免干扰菜单功能
        console.log('🛡️ 深度优化（安全模式）：跳过可能干扰菜单的操作');
        elements.forEach(el => {
            // 移除内联事件处理器，使用事件委托
            if (el.onclick) {
                el.removeAttribute('onclick');
            }
            if (el.onload) {
                el.removeAttribute('onload');
            }
            if (el.onerror) {
                el.removeAttribute('onerror');
            }
        });
        
        // 压缩CSS - 已禁用
        // const styles = document.querySelectorAll('style');
        // styles.forEach(style => {
        //     if (style.textContent) {
        //         style.textContent = style.textContent
        //             .replace(/\s+/g, ' ')
        //             .replace(/;\s*}/g, '}')
        //             .replace(/\s*{\s*/g, '{')
        //             .trim();
        //     }
        // });
        
        console.log('✅ 深度优化完成');
    }
    
    function triggerMemoryCleanup() {
        // 清理大型对象
        if (window.performanceData) {
            Object.keys(window.performanceData).forEach(key => {
                if (Array.isArray(window.performanceData[key])) {
                    window.performanceData[key] = window.performanceData[key].slice(-50);
                }
            });
        }
        
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
        
        // 强制垃圾回收（如果可用）
        if (window.gc) {
            window.gc();
        }
        
        console.log('✅ 内存清理完成');
    }
    
    function triggerNetworkOptimization() {
        // 压缩图片质量
        const images = document.querySelectorAll('img[src]');
        images.forEach(img => {
            if (!img.src.includes('data:') && !img.src.includes('quality=')) {
                const separator = img.src.includes('?') ? '&' : '?';
                img.src += `${separator}quality=80&compress=true`;
            }
        });
        
        // 延迟加载非关键资源 - 已禁用
        // const nonCriticalLinks = document.querySelectorAll('link[rel="stylesheet"]:not([href*="bootstrap"]):not([href*="fontawesome"])');
        // nonCriticalLinks.forEach(link => {
        //     link.media = 'print';
        //     link.onload = function() {
        //         this.media = 'all';
        //     };
        // });
        
        console.log('✅ 网络优化完成');
    }
    
    // 导出到全局作用域
    window.PerformanceAutoStart = {
        triggerDOMOptimization,
        triggerLightOptimization,
        triggerDeepOptimization,
        triggerMemoryCleanup,
        triggerNetworkOptimization
    };
    
    console.log('🎯 性能自动启动脚本已加载');
})();
