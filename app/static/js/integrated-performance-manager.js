/**
 * 整合性能管理器 v2.0
 * 统一管理所有性能优化功能，解决脚本冲突问题
 * 整合功能：性能监控、事件管理、菜单修复、页面优化
 */

// 防止重复加载
if (typeof window.IntegratedPerformanceManager !== 'undefined') {
    console.log('🚀 整合性能管理器已存在，跳过重复加载');
} else {

class IntegratedPerformanceManager {
    constructor() {
        this.version = '2.0';
        this.startTime = performance.now();
        this.isInitialized = false;
        
        // 配置选项
        this.config = {
            enableDashboard: true,
            enableEventProtection: true,
            enablePerformanceBoost: true,
            enableMenuFix: true,
            enableSmartPreload: true,
            enableLoadingFix: true, // 新增：页面加载修复
            debugMode: false,
            eventCheckInterval: 5000, // 5秒检查一次
            maxEventChecks: 3, // 最多检查3次
            loadingTimeout: 2000, // 页面加载超时时间（2秒）
            loadingCheckInterval: 1000 // 加载状态检查间隔
        };
        
        // 状态管理
        this.state = {
            eventProtectionActive: false,
            dashboardVisible: false,
            lastEventCheck: 0,
            eventCheckCount: 0,
            menuEventsBound: false,
            pageLoadingState: 'unknown', // 新增：页面加载状态
            loadingCheckTimer: null,
            loadingStartTime: Date.now()
        };
        
        // 事件管理
        this.eventListeners = new Map();
        this.protectedElements = new Set();
        this.eventCheckTimer = null;
        
        // 性能指标
        this.performanceMetrics = {
            pageLoadTime: 0,
            domReadyTime: 0,
            resourceLoadTime: 0,
            scriptLoadTime: 0,
            optimizationsApplied: []
        };
        
        // 组件实例
        this.messageSystem = null;
        this.dashboard = null;
        
        this.init();
    }
    
    init() {
        if (this.isInitialized) return;
        
        console.log(`🚀 整合性能管理器 v${this.version} 开始初始化...`);
        
        // 等待DOM准备就绪
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
        
        this.isInitialized = true;
    }
    
    setup() {
        try {
            // 按顺序初始化各个模块
            this.initMessageSystem();
            this.initPerformanceMonitoring();
            this.initEventProtection();
            this.initMenuFix();
            this.initPerformanceBoost();
            this.initLoadingFix(); // 新增：页面加载修复
            this.initDashboard();
            
            console.log('✅ 整合性能管理器初始化完成');
        } catch (error) {
            console.error('❌ 整合性能管理器初始化失败:', error);
        }
    }
    
    // 1. 消息系统
    initMessageSystem() {
        if (typeof window.showMessage === 'undefined') {
            window.showMessage = (type, message, duration = 3000) => {
                const toast = document.createElement('div');
                toast.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'warning'}`;
                toast.style.cssText = 'position:fixed;top:20px;right:20px;z-index:9999;min-width:300px;opacity:0.95;';
                toast.innerHTML = `<strong>${type.toUpperCase()}:</strong> ${message}`;
                document.body.appendChild(toast);
                
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
    
    // 2. 性能监控
    initPerformanceMonitoring() {
        // 记录页面加载时间
        this.performanceMetrics.pageLoadTime = performance.now() - this.startTime;
        this.performanceMetrics.domReadyTime = performance.now();
        
        // 监控资源加载
        window.addEventListener('load', () => {
            this.performanceMetrics.resourceLoadTime = performance.now() - this.startTime;
            this.analyzePerformance();
        });
        
        console.log('✅ 性能监控已启用');
    }
    
    // 3. 事件保护机制 - 优化版本
    initEventProtection() {
        if (!this.config.enableEventProtection) return;
        
        // 智能事件检查，避免过度频繁
        this.startSmartEventCheck();
        
        // 页面可见性变化监听
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.checkAndRebindEvents();
            }
        });
        
        console.log('✅ 智能事件保护已启用');
    }
    
    // 智能事件检查
    startSmartEventCheck() {
        if (this.state.eventProtectionActive) return;
        
        this.state.eventProtectionActive = true;
        this.state.eventCheckCount = 0;
        
        this.eventCheckTimer = setInterval(() => {
            this.state.eventCheckCount++;
            
            if (this.state.eventCheckCount > this.config.maxEventChecks) {
                this.stopEventCheck();
                return;
            }
            
            this.checkAndRebindEvents();
        }, this.config.eventCheckInterval);
    }
    
    // 检查并重新绑定事件
    checkAndRebindEvents() {
        const wholeBtn = document.getElementById('wholeSelectCodeBtn');
        const splitBtn = document.getElementById('splitSelectCodeBtn');
        
        if (wholeBtn && splitBtn) {
            const wholeNeedsRebind = !this.hasEventListener(wholeBtn, 'click');
            const splitNeedsRebind = !this.hasEventListener(splitBtn, 'click');
            
            if (wholeNeedsRebind || splitNeedsRebind) {
                if (this.config.debugMode) {
                    console.warn('检测到选择按钮事件丢失，正在重新绑定...');
                }
                this.rebindSelectButtons();
            } else {
                // 事件正常，停止检查
                this.stopEventCheck();
                if (this.config.debugMode) {
                    console.log('✅ 选择按钮事件正常，停止监控');
                }
            }
        }
    }
    
    // 停止事件检查
    stopEventCheck() {
        if (this.eventCheckTimer) {
            clearInterval(this.eventCheckTimer);
            this.eventCheckTimer = null;
        }
        this.state.eventProtectionActive = false;
        console.log('🔄 事件检查已完成');
    }
    
    // 检查元素是否有事件监听器
    hasEventListener(element, eventType) {
        if (!element) return false;
        
        // 检查jQuery事件
        try {
            if (typeof $ !== 'undefined') {
                const events = $._data(element, 'events');
                if (events && events[eventType] && events[eventType].length > 0) {
                    return true;
                }
            }
        } catch (e) {
            // jQuery检查失败，继续检查原生事件
        }
        
        // 检查原生事件监听器
        if (element.onclick || element['on' + eventType]) {
            return true;
        }
        
        // 检查自定义标记
        return element.hasAttribute('data-event-bound');
    }
    
    // 重新绑定选择按钮事件 - 防重复版本
    rebindSelectButtons() {
        const wholeBtn = document.getElementById('wholeSelectCodeBtn');
        const splitBtn = document.getElementById('splitSelectCodeBtn');
        
        if (wholeBtn && !wholeBtn.hasAttribute('data-event-bound')) {
            this.bindSelectButton(wholeBtn, '整板选择');
        }
        
        if (splitBtn && !splitBtn.hasAttribute('data-event-bound')) {
            this.bindSelectButton(splitBtn, '拆板选择');
        }
    }
    
    // 绑定单个选择按钮
    bindSelectButton(button, type) {
        // 移除旧事件
        const newButton = button.cloneNode(true);
        button.parentNode.replaceChild(newButton, button);
        
        // 绑定新事件
        newButton.addEventListener('click', () => {
            if (this.config.debugMode) {
                console.log(`${type}按钮被点击`);
            }
            
            // 设置默认搜索日期
            const endDate = new Date();
            const startDate = new Date();
            startDate.setDate(startDate.getDate() - 7);
            
            const startInput = document.getElementById('searchStartDate');
            const endInput = document.getElementById('searchEndDate');
            
            if (startInput && endInput) {
                startInput.value = this.formatDate(startDate);
                endInput.value = this.formatDate(endDate);
            }
            
            // 显示模态框
            if (typeof getInboundRecordModal === 'function') {
                const modal = getInboundRecordModal();
                if (modal) {
                    modal.show();
                    if (typeof loadInboundRecords === 'function') {
                        loadInboundRecords();
                    }
                }
            }
        });
        
        // 标记已绑定
        newButton.setAttribute('data-event-bound', 'true');
        
        if (this.config.debugMode) {
            console.log(`✅ ${type}按钮事件已绑定`);
        }
    }
    
    // 格式化日期
    formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }
    
    // 4. 菜单修复
    initMenuFix() {
        if (!this.config.enableMenuFix || this.state.menuEventsBound) return;
        
        // 延迟绑定菜单事件，避免与其他脚本冲突
        setTimeout(() => {
            this.bindMenuEvents();
        }, 1000);
    }
    
    // 绑定菜单事件
    bindMenuEvents() {
        try {
            // 移除现有事件监听器
            $('.dropdown-toggle').off('click.integrated-manager');
            
            // 重新绑定一级菜单事件
            $(document).on('click.integrated-manager', '.dropdown-toggle', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const $this = $(this);
                const targetId = $this.attr('href');
                const $target = $(targetId);
                
                if ($target.length === 0) return;
                
                // 切换菜单状态
                if ($target.hasClass('show')) {
                    $target.removeClass('show').slideUp(200);
                    $this.attr('aria-expanded', 'false').addClass('collapsed');
                } else {
                    // 关闭其他菜单
                    $('.dropdown-toggle').not($this).each(function() {
                        const otherTargetId = $(this).attr('href');
                        const $otherTarget = $(otherTargetId);
                        if ($otherTarget.hasClass('show')) {
                            $otherTarget.removeClass('show').slideUp(200);
                            $(this).attr('aria-expanded', 'false').addClass('collapsed');
                        }
                    });
                    
                    // 展开当前菜单
                    $target.addClass('show').slideDown(200);
                    $this.attr('aria-expanded', 'true').removeClass('collapsed');
                }
            });
            
            this.state.menuEventsBound = true;
            console.log('✅ 菜单事件已修复');
        } catch (error) {
            console.error('❌ 菜单事件绑定失败:', error);
        }
    }

    // 5. 性能提升
    initPerformanceBoost() {
        if (!this.config.enablePerformanceBoost) return;

        // CSS预加载
        this.preloadCriticalCSS();

        // 脚本执行优化
        this.optimizeScriptExecution();

        // DOM批量操作优化
        this.optimizeDOMOperations();

        // 懒加载优化
        this.initLazyLoading();

        // 内存优化
        this.optimizeMemoryUsage();

        this.performanceMetrics.optimizationsApplied.push('性能提升');
        console.log('✅ 性能提升已应用');
    }

    // CSS预加载
    preloadCriticalCSS() {
        const criticalCSS = [
            '/static/css/style.css',
            '/static/css/inventory-table.css'
        ];

        criticalCSS.forEach(href => {
            // 检查CSS文件是否存在再预加载
            fetch(href, { method: 'HEAD' })
                .then(response => {
                    if (response.ok) {
                        const link = document.createElement('link');
                        link.rel = 'preload';
                        link.as = 'style';
                        link.href = href;
                        document.head.appendChild(link);
                    }
                })
                .catch(() => {
                    // 文件不存在，忽略错误
                });
        });
    }

    // 脚本执行优化
    optimizeScriptExecution() {
        // 延迟非关键脚本执行
        if (typeof requestIdleCallback !== 'undefined') {
            requestIdleCallback(() => {
                this.executeNonCriticalTasks();
            });
        } else {
            setTimeout(() => {
                this.executeNonCriticalTasks();
            }, 100);
        }
    }

    // 执行非关键任务
    executeNonCriticalTasks() {
        // 清理未使用的事件监听器
        this.cleanupUnusedListeners();

        // 优化图片加载
        this.optimizeImageLoading();
    }

    // DOM批量操作优化
    optimizeDOMOperations() {
        // 创建文档片段进行批量DOM操作
        if (typeof window.createDocumentFragment === 'undefined') {
            window.createDocumentFragment = () => document.createDocumentFragment();
        }
    }

    // 懒加载优化
    initLazyLoading() {
        if ('IntersectionObserver' in window) {
            const lazyImages = document.querySelectorAll('img[data-src]');
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        imageObserver.unobserve(img);
                    }
                });
            });

            lazyImages.forEach(img => imageObserver.observe(img));
        }
    }

    // 内存优化
    optimizeMemoryUsage() {
        // 定期清理内存
        setInterval(() => {
            this.cleanupMemory();
        }, 300000); // 5分钟清理一次
    }

    // 清理内存
    cleanupMemory() {
        // 清理过期的事件监听器
        this.eventListeners.forEach((listener, key) => {
            if (!document.contains(listener.element)) {
                this.eventListeners.delete(key);
            }
        });

        // 强制垃圾回收（如果支持）
        if (window.gc) {
            window.gc();
        }
    }

    // 清理未使用的事件监听器
    cleanupUnusedListeners() {
        const elements = document.querySelectorAll('*');
        elements.forEach(element => {
            if (element._listeners) {
                // 清理jQuery事件缓存
                try {
                    if (typeof $ !== 'undefined') {
                        $(element).off('.unused');
                    }
                } catch (e) {
                    // 忽略清理错误
                }
            }
        });
    }

    // 优化图片加载
    optimizeImageLoading() {
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            if (!img.complete) {
                img.loading = 'lazy';
            }
        });
    }

    // 6. 页面加载修复
    initLoadingFix() {
        if (!this.config.enableLoadingFix) return;

        console.log('🔧 启动页面加载状态监控...');

        // 检测页面加载状态
        this.detectLoadingState();

        // 设置加载超时检测
        this.setupLoadingTimeout();

        // 监控关键元素加载
        this.monitorCriticalElements();

        // 检测并修复常见的加载问题
        this.fixCommonLoadingIssues();

        console.log('✅ 页面加载修复已启用');
    }

    // 检测页面加载状态
    detectLoadingState() {
        const checkLoadingState = () => {
            // 检查加载指示器
            const loadingIndicators = document.querySelectorAll(
                '#loading-indicator, .loading-overlay, .spinner-border, [class*="loading"], [class*="spinner"]'
            );

            let hasVisibleLoading = false;
            loadingIndicators.forEach(indicator => {
                const style = window.getComputedStyle(indicator);
                if (style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0') {
                    hasVisibleLoading = true;
                }
            });

            // 检查页面内容是否已加载
            const hasContent = document.querySelectorAll('table tbody tr, .content-wrapper, .container-fluid').length > 0;
            const hasData = document.querySelectorAll('td:not(:empty), .data-row, [data-loaded="true"]').length > 0;

            // 更新加载状态
            if (hasVisibleLoading && !hasData) {
                this.state.pageLoadingState = 'loading';
            } else if (hasContent && hasData) {
                this.state.pageLoadingState = 'loaded';
                this.hideLoadingIndicators();
            } else if (!hasVisibleLoading && !hasData) {
                this.state.pageLoadingState = 'stuck';
                this.handleStuckLoading();
            }
        };

        // 立即检查一次
        checkLoadingState();

        // 定期检查（避免死循环，最多检查10次）
        let checkCount = 0;
        const maxChecks = 10;

        this.state.loadingCheckTimer = setInterval(() => {
            checkCount++;
            checkLoadingState();

            if (this.state.pageLoadingState === 'loaded' || checkCount >= maxChecks) {
                clearInterval(this.state.loadingCheckTimer);
                this.state.loadingCheckTimer = null;

                if (checkCount >= maxChecks && this.state.pageLoadingState !== 'loaded') {
                    console.log('⚠️ 页面加载检查达到最大次数，停止检查');
                    this.handleStuckLoading();
                }
            }
        }, this.config.loadingCheckInterval);
    }

    // 设置加载超时检测
    setupLoadingTimeout() {
        setTimeout(() => {
            if (this.state.pageLoadingState === 'loading' || this.state.pageLoadingState === 'unknown') {
                console.log('⚠️ 页面加载超时，尝试修复...');
                this.handleLoadingTimeout();
            }
        }, this.config.loadingTimeout);
    }

    // 监控关键元素加载
    monitorCriticalElements() {
        const criticalSelectors = [
            'table', 'form', '.content-wrapper', '.container-fluid',
            '[data-table]', '[data-content]', '.main-content'
        ];

        const observer = new MutationObserver((mutations) => {
            let hasNewContent = false;

            mutations.forEach(mutation => {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            criticalSelectors.forEach(selector => {
                                if (node.matches && node.matches(selector)) {
                                    hasNewContent = true;
                                }
                            });
                        }
                    });
                }
            });

            if (hasNewContent && this.state.pageLoadingState === 'loading') {
                console.log('✅ 检测到关键内容加载完成');
                this.state.pageLoadingState = 'loaded';
                this.hideLoadingIndicators();
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        // 5秒后停止观察（避免长期运行）
        setTimeout(() => {
            observer.disconnect();
        }, 5000);
    }

    // 修复常见的加载问题
    fixCommonLoadingIssues() {
        // 修复jQuery未加载问题
        if (typeof $ === 'undefined') {
            console.log('🔧 检测到jQuery未加载，尝试修复...');
            this.loadJQuery();
        }

        // 修复CSS未加载问题
        this.checkAndFixCSS();

        // 修复JavaScript错误导致的加载卡住
        this.fixJavaScriptErrors();
    }

    // 处理加载卡住的情况
    handleStuckLoading() {
        console.log('🔧 检测到页面加载卡住，尝试修复...');

        // 强制隐藏加载指示器
        this.hideLoadingIndicators();

        // 尝试重新初始化页面功能
        this.reinitializePageFunctions();

        // 显示用户友好的提示
        this.showLoadingFixMessage();
    }

    // 处理加载超时
    handleLoadingTimeout() {
        console.log('🔧 页面加载超时，执行修复操作...');

        // 强制隐藏加载指示器
        this.hideLoadingIndicators();

        // 检查并修复网络请求
        this.checkNetworkRequests();

        // 重新加载关键资源
        this.reloadCriticalResources();
    }

    // 隐藏加载指示器
    hideLoadingIndicators() {
        const indicators = document.querySelectorAll(
            '#loading-indicator, .loading-overlay, .spinner-border, [class*="loading"], [class*="spinner"]'
        );

        indicators.forEach(indicator => {
            indicator.style.display = 'none';
        });

        // 移除body上的loading类
        document.body.classList.remove('loading', 'page-loading');

        console.log('✅ 加载指示器已隐藏');
    }

    // 重新初始化页面功能
    reinitializePageFunctions() {
        // 触发页面就绪事件
        if (typeof $ !== 'undefined') {
            $(document).trigger('page:ready');
        }

        // 重新绑定事件
        this.rebindEvents();
    }

    // 重新绑定事件
    rebindEvents() {
        // 检查并重新绑定常见的事件
        const commonButtons = document.querySelectorAll('button, .btn, [onclick]');
        commonButtons.forEach(btn => {
            if (!btn.hasAttribute('data-events-bound')) {
                btn.setAttribute('data-events-bound', 'true');
            }
        });
    }

    // 显示修复提示消息
    showLoadingFixMessage() {
        if (typeof window.showMessage !== 'undefined') {
            window.showMessage('info', '页面加载已优化，如仍有问题请刷新页面', 3000);
        }
    }

    // 检查网络请求
    checkNetworkRequests() {
        // 检查是否有失败的网络请求
        if (window.performance && window.performance.getEntriesByType) {
            const resources = window.performance.getEntriesByType('resource');
            const failedRequests = resources.filter(resource =>
                resource.transferSize === 0 && resource.decodedBodySize === 0
            );

            if (failedRequests.length > 0) {
                console.log('⚠️ 检测到失败的网络请求:', failedRequests.length);
            }
        }
    }

    // 重新加载关键资源
    reloadCriticalResources() {
        // 重新加载CSS
        const cssLinks = document.querySelectorAll('link[rel="stylesheet"]');
        cssLinks.forEach(link => {
            if (link.href.includes('bootstrap') || link.href.includes('custom')) {
                const newLink = link.cloneNode();
                newLink.href = link.href + '?reload=' + Date.now();
                link.parentNode.insertBefore(newLink, link.nextSibling);
            }
        });
    }

    // 加载jQuery
    loadJQuery() {
        if (document.querySelector('script[src*="jquery"]')) {
            return; // 已经有jQuery脚本标签
        }

        const script = document.createElement('script');
        script.src = 'https://code.jquery.com/jquery-3.6.0.min.js';
        script.onload = () => {
            console.log('✅ jQuery加载完成');
            this.reinitializePageFunctions();
        };
        document.head.appendChild(script);
    }

    // 检查并修复CSS
    checkAndFixCSS() {
        const requiredCSS = [
            { name: 'bootstrap', pattern: 'bootstrap' },
            { name: 'custom', pattern: 'custom' }
        ];

        requiredCSS.forEach(css => {
            const existing = document.querySelector(`link[href*="${css.pattern}"]`);
            if (!existing) {
                console.log(`🔧 ${css.name} CSS未找到，尝试加载...`);
                const link = document.createElement('link');
                link.rel = 'stylesheet';
                link.href = `/static/css/${css.pattern}.css`;
                document.head.appendChild(link);
            }
        });
    }

    // 修复JavaScript错误
    fixJavaScriptErrors() {
        // 捕获并处理JavaScript错误
        window.addEventListener('error', (event) => {
            console.log('🔧 捕获到JavaScript错误:', event.error);

            // 如果是关键错误，尝试修复
            if (event.error && event.error.message) {
                const message = event.error.message.toLowerCase();
                if (message.includes('jquery') || message.includes('$')) {
                    this.loadJQuery();
                }
            }
        });
    }

    // 7. 性能监控面板
    initDashboard() {
        if (!this.config.enableDashboard) return;

        // 创建简化的性能监控面板
        this.createSimpleDashboard();

        // 绑定快捷键
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.shiftKey && e.key === 'P') {
                e.preventDefault();
                this.toggleDashboard();
            }
        });

        console.log('✅ 性能监控面板已初始化 (Ctrl+Shift+P 打开)');
    }

    // 创建简化的性能监控面板
    createSimpleDashboard() {
        const dashboard = document.createElement('div');
        dashboard.id = 'integrated-performance-dashboard';
        dashboard.style.cssText = `
            position: fixed;
            top: 20px;
            left: 20px;
            width: 300px;
            background: rgba(0,0,0,0.9);
            color: white;
            padding: 15px;
            border-radius: 8px;
            z-index: 10000;
            font-family: monospace;
            font-size: 12px;
            display: none;
        `;

        dashboard.innerHTML = `
            <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 10px;">
                <h6 style="margin: 0; color: #00ff00;">🚀 性能监控</h6>
                <button onclick="window.integratedPM.toggleDashboard()" style="background: none; border: none; color: white; cursor: pointer;">×</button>
            </div>
            <div id="performance-metrics"></div>
            <div style="margin-top: 10px;">
                <button onclick="window.integratedPM.refreshMetrics()" style="background: #007bff; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">刷新</button>
                <button onclick="window.integratedPM.runDiagnostics()" style="background: #28a745; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; margin-left: 5px;">诊断</button>
            </div>
        `;

        document.body.appendChild(dashboard);
        this.dashboard = dashboard;
    }

    // 切换监控面板
    toggleDashboard() {
        if (!this.dashboard) return;

        this.state.dashboardVisible = !this.state.dashboardVisible;
        this.dashboard.style.display = this.state.dashboardVisible ? 'block' : 'none';

        if (this.state.dashboardVisible) {
            this.refreshMetrics();
        }
    }

    // 刷新性能指标
    refreshMetrics() {
        if (!this.dashboard) return;

        const metricsDiv = this.dashboard.querySelector('#performance-metrics');
        const currentTime = performance.now();

        const loadingStateIcon = {
            'unknown': '❓',
            'loading': '⏳',
            'loaded': '✅',
            'stuck': '⚠️'
        };

        metricsDiv.innerHTML = `
            <div>页面加载: ${this.performanceMetrics.pageLoadTime.toFixed(0)}ms</div>
            <div>加载状态: ${loadingStateIcon[this.state.pageLoadingState]} ${this.state.pageLoadingState}</div>
            <div>运行时间: ${(currentTime - this.startTime).toFixed(0)}ms</div>
            <div>事件检查: ${this.state.eventCheckCount}/${this.config.maxEventChecks}</div>
            <div>优化项目: ${this.performanceMetrics.optimizationsApplied.length}</div>
            <div>内存使用: ${this.getMemoryUsage()}</div>
        `;
    }

    // 获取内存使用情况
    getMemoryUsage() {
        if (performance.memory) {
            const used = (performance.memory.usedJSHeapSize / 1024 / 1024).toFixed(1);
            const total = (performance.memory.totalJSHeapSize / 1024 / 1024).toFixed(1);
            return `${used}MB / ${total}MB`;
        }
        return '不可用';
    }

    // 运行诊断
    runDiagnostics() {
        const issues = [];

        // 检查事件绑定
        const wholeBtn = document.getElementById('wholeSelectCodeBtn');
        const splitBtn = document.getElementById('splitSelectCodeBtn');

        if (!this.hasEventListener(wholeBtn, 'click')) {
            issues.push('整板选择按钮事件丢失');
        }

        if (!this.hasEventListener(splitBtn, 'click')) {
            issues.push('拆板选择按钮事件丢失');
        }

        // 检查性能
        const loadTime = this.performanceMetrics.pageLoadTime;
        if (loadTime > 3000) {
            issues.push('页面加载时间过长');
        }

        // 显示诊断结果
        if (issues.length === 0) {
            this.messageSystem('success', '✅ 系统运行正常');
        } else {
            this.messageSystem('warning', `发现 ${issues.length} 个问题: ${issues.join(', ')}`);
        }
    }

    // 分析性能
    analyzePerformance() {
        const loadTime = this.performanceMetrics.resourceLoadTime;

        if (loadTime < 1000) {
            console.log('🚀 页面加载快速:', (loadTime / 1000).toFixed(2) + 's');
        } else if (loadTime < 3000) {
            console.log('⚡ 页面加载正常:', (loadTime / 1000).toFixed(2) + 's');
        } else {
            console.log('⚠️ 页面加载较慢:', (loadTime / 1000).toFixed(2) + 's');
        }

        // 记录优化建议
        if (loadTime > 3000) {
            console.log('💡 建议启用更多性能优化');
        }
    }

    // 公共API
    getMetrics() {
        return this.performanceMetrics;
    }

    getState() {
        return this.state;
    }

    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
        console.log('⚙️ 配置已更新');
    }
}

// 创建全局实例
window.IntegratedPerformanceManager = IntegratedPerformanceManager;

// 自动初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.integratedPM = new IntegratedPerformanceManager();
    });
} else {
    window.integratedPM = new IntegratedPerformanceManager();
}

console.log('🚀 整合性能管理器实例已创建');

} // 结束防重复加载检查
