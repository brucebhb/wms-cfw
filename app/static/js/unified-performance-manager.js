/**
 * 统一性能管理器 - 整合所有性能监控和优化功能
 * 替代: page-load-optimizer.js, simple-performance-monitor.js, menu-event-manager.js 等
 */

class UnifiedPerformanceManager {
    constructor() {
        this.startTime = performance.now();
        this.isInitialized = false;
        this.menuEventsBound = false;
        this.messageSystem = null;
        
        // 性能阈值配置
        this.thresholds = {
            fast: 1000,      // 1秒以下为快速
            normal: 3000,    // 3秒以下为正常
            slow: 5000       // 5秒以上为慢速
        };
        
        this.init();
    }
    
    init() {
        if (this.isInitialized) return;
        
        // 等待DOM准备就绪
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
        
        this.isInitialized = true;
    }
    
    setup() {
        this.initMessageSystem();
        // 暂时禁用菜单事件处理，使用原来的menu-event-manager.js
        // this.initMenuEvents();
        this.initPerformanceMonitoring();
        this.optimizePageLoad();
    }
    
    // 初始化消息系统
    initMessageSystem() {
        if (typeof window.showMessage === 'undefined') {
            window.showMessage = (type, message, duration = 3000) => {
                const toast = document.createElement('div');
                toast.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'warning'}`;
                toast.style.cssText = 'position:fixed;top:20px;right:20px;z-index:9999;min-width:300px;opacity:0.95;';
                toast.innerHTML = `<strong>${type.toUpperCase()}:</strong> ${message}`;
                document.body.appendChild(toast);
                
                // 自动移除
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.remove();
                    }
                }, duration);
            };
        }
        
        this.messageSystem = window.showMessage;
        console.log('✅ 消息系统已初始化');
    }
    
    // 初始化菜单事件（完整版）
    initMenuEvents() {
        if (this.menuEventsBound) return;

        try {
            const self = this;

            // 移除现有的事件监听器
            $('.dropdown-toggle').off('click.bs.collapse');
            $(document).off('click.menu-manager');
            $(document).off('click.submenu-manager');

            // 一级菜单事件 - 使用原来的逻辑
            $(document).on('click.menu-manager', '.dropdown-toggle', function(e) {
                e.preventDefault();
                e.stopPropagation();

                const $this = $(this);
                const targetId = $this.attr('href');
                const $target = $(targetId);

                if ($target.length === 0) {
                    console.warn('菜单目标不存在:', targetId);
                    return;
                }

                // 先关闭其他展开的菜单
                $('.dropdown-toggle').not($this).each(function() {
                    const otherTargetId = $(this).attr('href');
                    const $otherTarget = $(otherTargetId);
                    if ($otherTarget.hasClass('show')) {
                        $otherTarget.removeClass('show');
                        $(this).attr('aria-expanded', 'false').addClass('collapsed');
                        $otherTarget.slideUp(200);
                    }
                });

                // 切换当前菜单状态
                self.toggleMenu($this, $target);

                console.log(`一级菜单点击: ${targetId}`);
            });

            // 二级菜单事件
            $(document).on('click.submenu-manager', '.submenu-header', function(e) {
                e.preventDefault();
                e.stopPropagation();

                const $this = $(this);
                const targetId = $this.data('target');
                const $target = $('#' + targetId);

                if ($target.length === 0) {
                    return;
                }

                // 切换二级菜单状态
                self.toggleSubmenu($this, $target, targetId);

                console.log(`二级菜单点击: ${targetId}`);
            });

            // 普通链接点击事件
            $(document).on('click', '.nav-link:not(.dropdown-toggle):not(.submenu-header)', function(e) {
                const href = $(this).attr('href');
                if (href && href !== '#' && !href.startsWith('javascript:')) {
                    // 允许正常的链接跳转
                    console.log('导航到:', href);
                }
            });

            // 侧边栏切换
            $(document).on('click', '[data-bs-toggle="sidebar"]', function() {
                $('body').toggleClass('sidebar-collapsed');
            });

            this.menuEventsBound = true;
            console.log('✅ 菜单事件已绑定');

        } catch (error) {
            console.warn('菜单事件绑定失败:', error);
        }
    }
    
    // 切换菜单状态
    toggleMenu($trigger, $target) {
        const isExpanded = $trigger.attr('aria-expanded') === 'true';

        if (isExpanded) {
            // 收起菜单
            $target.removeClass('show');
            $trigger.attr('aria-expanded', 'false');
            $trigger.addClass('collapsed');
            $target.slideUp(200);
        } else {
            // 展开菜单
            $target.addClass('show');
            $trigger.attr('aria-expanded', 'true');
            $trigger.removeClass('collapsed');
            $target.slideDown(200);
        }
    }

    // 切换二级菜单状态
    toggleSubmenu($trigger, $target, targetId) {
        const isCollapsed = $target.hasClass('collapsed');

        if (isCollapsed) {
            $target.removeClass('collapsed');
            $trigger.removeClass('collapsed');
        } else {
            $target.addClass('collapsed');
            $trigger.addClass('collapsed');
        }
    }

    // 性能监控
    initPerformanceMonitoring() {
        // 页面加载完成监控
        $(window).on('load', () => {
            const loadTime = performance.now() - this.startTime;
            this.reportPerformance(loadTime);
        });
        
        // 资源加载监控
        this.monitorResources();
    }
    
    // 报告性能数据
    reportPerformance(loadTime) {
        const seconds = (loadTime / 1000).toFixed(2);
        
        if (loadTime < this.thresholds.fast) {
            console.log(`🚀 页面加载快速: ${seconds}s`);
        } else if (loadTime < this.thresholds.normal) {
            console.log(`⚡ 页面加载正常: ${seconds}s`);
        } else if (loadTime < this.thresholds.slow) {
            console.warn(`⚠️ 页面加载较慢: ${seconds}s`);
            if (this.messageSystem) {
                this.messageSystem('warning', `页面加载时间: ${seconds}s，建议优化`, 3000);
            }
        } else {
            console.error(`🐌 页面加载过慢: ${seconds}s`);
            if (this.messageSystem) {
                this.messageSystem('error', `页面加载过慢: ${seconds}s，请检查网络`, 5000);
            }
        }
    }
    
    // 监控资源加载
    monitorResources() {
        if ('PerformanceObserver' in window) {
            try {
                const observer = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    entries.forEach(entry => {
                        if (entry.duration > 2000) { // 超过2秒的资源
                            console.warn(`慢速资源: ${entry.name} (${(entry.duration/1000).toFixed(2)}s)`);
                        }
                    });
                });
                
                observer.observe({ entryTypes: ['resource'] });
            } catch (error) {
                console.warn('性能监控初始化失败:', error);
            }
        }
    }
    
    // 页面加载优化
    optimizePageLoad() {
        // 预加载关键资源
        this.preloadCriticalResources();
        
        // 延迟加载非关键脚本
        this.deferNonCriticalScripts();
        
        // 优化图片加载
        this.optimizeImages();
    }
    
    // 预加载关键资源（智能预加载）
    preloadCriticalResources() {
        // 智能预加载关键CSS和JS资源
        const criticalResources = [
            // 只预加载确实需要的CDN资源
            'https://cdn.bootcdn.net/ajax/libs/twitter-bootstrap/5.3.0/css/bootstrap.min.css',
            'https://cdn.bootcdn.net/ajax/libs/font-awesome/6.4.0/css/all.min.css'
        ];

        criticalResources.forEach(url => {
            // 检查资源是否已经加载
            const existing = document.querySelector(`link[href="${url}"], script[src="${url}"]`);
            if (!existing) {
                const link = document.createElement('link');
                link.rel = 'prefetch';
                link.href = url;
                link.onload = () => console.log(`✅ 预加载成功: ${url}`);
                link.onerror = () => console.warn(`❌ 预加载失败: ${url}`);
                document.head.appendChild(link);
            }
        });

        console.log('✅ 智能预加载已启用');
    }
    
    // 延迟加载非关键脚本
    deferNonCriticalScripts() {
        // 延迟加载大型库
        setTimeout(() => {
            const scripts = document.querySelectorAll('script[data-defer="true"]');
            scripts.forEach(script => {
                const newScript = document.createElement('script');
                newScript.src = script.dataset.src;
                newScript.async = true;
                document.head.appendChild(newScript);
            });
        }, 100);
    }
    
    // 优化图片加载
    optimizeImages() {
        // 懒加载图片
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        if (img.dataset.src) {
                            img.src = img.dataset.src;
                            img.removeAttribute('data-src');
                            imageObserver.unobserve(img);
                        }
                    }
                });
            });
            
            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        }
    }
    
    // 清理和重置
    cleanup() {
        if (this.messageSystem) {
            // 清理现有的toast消息
            document.querySelectorAll('.alert').forEach(alert => {
                if (alert.style.position === 'fixed') {
                    alert.remove();
                }
            });
        }
    }
    
    // 获取性能报告
    getPerformanceReport() {
        const currentTime = performance.now();
        const totalTime = currentTime - this.startTime;
        
        return {
            totalLoadTime: totalTime,
            isOptimal: totalTime < this.thresholds.normal,
            recommendation: totalTime > this.thresholds.slow ? 
                '建议优化页面资源加载' : '性能表现良好'
        };
    }
}

// 全局初始化
window.UnifiedPerformanceManager = UnifiedPerformanceManager;

// 自动启动
// 立即初始化或等待DOM加载
function initUnifiedPerformanceManager() {
    if (!window.unifiedPerformanceManager) {
        window.unifiedPerformanceManager = new UnifiedPerformanceManager();
        // 保持向后兼容
        window.performanceManager = window.unifiedPerformanceManager;
        console.log('🚀 统一性能管理器实例已创建');
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initUnifiedPerformanceManager);
} else {
    // DOM已经加载完成，立即初始化
    initUnifiedPerformanceManager();
}

// 兼容性支持
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UnifiedPerformanceManager;
}
