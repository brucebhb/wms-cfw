/**
 * SPA路由系统 - 将现有多页面应用转换为单页应用
 * 不修改任何现有页面，通过AJAX加载内容
 */

class SPARouter {
    constructor() {
        this.routes = new Map();
        this.currentRoute = '';
        this.contentArea = null;
        this.sidebar = null;
        this.isInitialized = false;
        this.loadingIndicator = null;
        this.pageCache = new Map(); // 页面缓存
        this.maxCacheSize = 10; // 最大缓存页面数
        
        console.log('🚀 SPA路由系统初始化');
    }
    
    /**
     * 初始化路由系统
     */
    init() {
        if (this.isInitialized) return;
        
        try {
            this.setupDOM();
            this.registerDefaultRoutes();
            this.bindEvents();
            this.createLoadingIndicator();
            this.interceptNavigation();
            this.handleInitialRoute();
            
            this.isInitialized = true;
            console.log('✅ SPA路由系统启动成功');
            
            // 显示用户提示
            this.showUserTip();
            
        } catch (error) {
            console.error('❌ SPA路由系统初始化失败:', error);
        }
    }
    
    /**
     * 设置DOM结构
     */
    setupDOM() {
        // 查找内容区域
        this.contentArea = document.querySelector('.main-content') || 
                          document.querySelector('#main-content') ||
                          document.querySelector('main') ||
                          document.querySelector('.container-fluid .row .col-md-9') ||
                          document.querySelector('.container-fluid .row .col-lg-10');
        
        if (!this.contentArea) {
            // 如果找不到，创建一个内容区域
            const body = document.body;
            const wrapper = document.createElement('div');
            wrapper.className = 'spa-wrapper';
            wrapper.innerHTML = body.innerHTML;
            body.innerHTML = '';
            body.appendChild(wrapper);
            
            this.contentArea = wrapper;
        }
        
        // 查找侧边栏
        this.sidebar = document.querySelector('#sidebar') ||
                      document.querySelector('.sidebar') ||
                      document.querySelector('.col-md-3') ||
                      document.querySelector('.col-lg-2');
        
        console.log('📍 DOM结构设置完成', {
            contentArea: !!this.contentArea,
            sidebar: !!this.sidebar
        });
    }
    
    /**
     * 注册默认路由
     */
    registerDefaultRoutes() {
        // 自动发现现有的导航链接并注册路由
        const navLinks = document.querySelectorAll('a[href]');
        
        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            
            // 跳过外部链接、锚点链接、JavaScript链接
            if (this.isInternalRoute(href)) {
                this.route(href, () => this.loadPage(href));
                console.log('📝 注册路由:', href);
            }
        });
        
        // 注册特殊路由
        this.route('/', () => this.loadPage('/'));
        this.route('/index', () => this.loadPage('/'));
    }
    
    /**
     * 判断是否为内部路由
     */
    isInternalRoute(href) {
        if (!href) return false;
        
        // 排除的链接类型
        const excludePatterns = [
            /^#/,           // 锚点链接
            /^javascript:/i, // JavaScript链接
            /^mailto:/i,    // 邮件链接
            /^tel:/i,       // 电话链接
            /^http/i,       // 外部链接
            /\.(pdf|doc|xls|zip|rar)$/i, // 文件下载
            /^\/static\//,  // 静态文件
            /^\/api\//,     // API接口
            /logout/i       // 登出链接
        ];
        
        return !excludePatterns.some(pattern => pattern.test(href));
    }
    
    /**
     * 注册路由
     */
    route(path, handler) {
        this.routes.set(path, handler);
    }
    
    /**
     * 绑定事件
     */
    bindEvents() {
        // 拦截所有链接点击
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href]');
            if (link && this.shouldInterceptLink(link, e)) {
                e.preventDefault();
                e.stopPropagation();
                
                const href = link.getAttribute('href');
                this.navigate(href);
                
                // 更新菜单状态
                this.updateMenuState(link);
            }
        });
        
        // 监听浏览器前进后退
        window.addEventListener('popstate', (e) => {
            const path = window.location.pathname + window.location.search;
            this.loadRoute(path, false); // false表示不更新历史记录
        });
        
        // 监听表单提交
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (this.shouldInterceptForm(form)) {
                e.preventDefault();
                this.handleFormSubmit(form);
            }
        });
    }
    
    /**
     * 判断是否应该拦截链接
     */
    shouldInterceptLink(link, event) {
        const href = link.getAttribute('href');
        
        // 不拦截的情况
        if (!this.isInternalRoute(href)) return false;
        if (event.ctrlKey || event.metaKey || event.shiftKey) return false; // 修饰键
        if (link.target === '_blank') return false; // 新窗口打开
        if (link.hasAttribute('download')) return false; // 下载链接
        
        return true;
    }
    
    /**
     * 创建加载指示器
     */
    createLoadingIndicator() {
        this.loadingIndicator = document.createElement('div');
        this.loadingIndicator.className = 'spa-loading';
        this.loadingIndicator.innerHTML = `
            <div class="spa-loading-content">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <div class="mt-2">页面加载中...</div>
            </div>
        `;
        
        // 添加样式
        const style = document.createElement('style');
        style.textContent = `
            .spa-loading {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(255, 255, 255, 0.9);
                display: none;
                align-items: center;
                justify-content: center;
                z-index: 9999;
            }
            .spa-loading.show {
                display: flex;
            }
            .spa-loading-content {
                text-align: center;
                padding: 20px;
                background: white;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }
        `;
        document.head.appendChild(style);
        document.body.appendChild(this.loadingIndicator);
    }
    
    /**
     * 显示加载状态
     */
    showLoading() {
        if (this.loadingIndicator) {
            this.loadingIndicator.classList.add('show');
        }
    }
    
    /**
     * 隐藏加载状态
     */
    hideLoading() {
        if (this.loadingIndicator) {
            this.loadingIndicator.classList.remove('show');
        }
    }
    
    /**
     * 导航到指定路径
     */
    navigate(path, updateHistory = true) {
        console.log('🧭 导航到:', path);
        
        if (updateHistory && path !== this.currentRoute) {
            history.pushState({ path }, '', path);
        }
        
        this.loadRoute(path, updateHistory);
    }
    
    /**
     * 加载路由
     */
    loadRoute(path, updateHistory = true) {
        const handler = this.routes.get(path);
        
        if (handler) {
            this.currentRoute = path;
            handler();
        } else {
            // 尝试加载页面
            this.loadPage(path);
        }
    }
    
    /**
     * 加载页面内容
     */
    async loadPage(path) {
        try {
            console.log('📄 加载页面:', path);
            
            // 检查缓存
            if (this.pageCache.has(path)) {
                console.log('💾 从缓存加载页面:', path);
                this.renderPage(this.pageCache.get(path));
                return;
            }
            
            this.showLoading();
            
            const response = await fetch(path, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-SPA-Request': 'true'
                }
            });
            
            if (response.ok) {
                const html = await response.text();
                
                // 缓存页面内容
                this.cachePageContent(path, html);
                
                // 渲染页面
                this.renderPage(html);
                
                console.log('✅ 页面加载成功:', path);
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
        } catch (error) {
            console.error('❌ 页面加载失败:', error);
            this.showError('页面加载失败，请刷新页面重试');
        } finally {
            this.hideLoading();
        }
    }
    
    /**
     * 缓存页面内容
     */
    cachePageContent(path, html) {
        // 如果缓存已满，删除最旧的条目
        if (this.pageCache.size >= this.maxCacheSize) {
            const firstKey = this.pageCache.keys().next().value;
            this.pageCache.delete(firstKey);
        }
        
        this.pageCache.set(path, html);
        console.log('💾 页面已缓存:', path);
    }
    
    /**
     * 渲染页面内容
     */
    renderPage(html) {
        if (!this.contentArea) return;

        // 提取页面内容
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;

        // 尝试提取主要内容区域
        let content = tempDiv.querySelector('.main-content') ||
                     tempDiv.querySelector('#main-content') ||
                     tempDiv.querySelector('main') ||
                     tempDiv.querySelector('.container-fluid') ||
                     tempDiv;

        // 更新内容区域
        this.contentArea.innerHTML = content.innerHTML;

        // 执行页面脚本
        this.executePageScripts();

        // 重新绑定事件
        this.rebindPageEvents();

        // 滚动到顶部
        window.scrollTo(0, 0);
    }

    /**
     * 执行页面脚本
     */
    executePageScripts() {
        // 查找并执行页面中的脚本
        const scripts = this.contentArea.querySelectorAll('script');
        scripts.forEach(script => {
            try {
                if (script.src) {
                    // 外部脚本
                    const newScript = document.createElement('script');
                    newScript.src = script.src;
                    newScript.async = false;
                    document.head.appendChild(newScript);
                } else {
                    // 内联脚本
                    eval(script.textContent);
                }
            } catch (error) {
                console.warn('脚本执行失败:', error);
            }
        });
    }

    /**
     * 重新绑定页面事件
     */
    rebindPageEvents() {
        // 重新初始化常用组件
        try {
            // Bootstrap组件
            if (typeof bootstrap !== 'undefined') {
                // 重新初始化tooltips
                const tooltips = this.contentArea.querySelectorAll('[data-bs-toggle="tooltip"]');
                tooltips.forEach(el => new bootstrap.Tooltip(el));

                // 重新初始化popovers
                const popovers = this.contentArea.querySelectorAll('[data-bs-toggle="popover"]');
                popovers.forEach(el => new bootstrap.Popover(el));
            }

            // 重新初始化表单验证
            if (typeof $ !== 'undefined') {
                $(this.contentArea).find('form').each(function() {
                    // 重新绑定表单事件
                    $(this).off('.spa').on('submit.spa', function(e) {
                        // 表单提交处理
                    });
                });
            }

        } catch (error) {
            console.warn('重新绑定事件失败:', error);
        }
    }

    /**
     * 更新菜单状态
     */
    updateMenuState(activeLink) {
        // 移除所有活动状态
        document.querySelectorAll('.nav-link, .dropdown-item, .list-group-item').forEach(link => {
            link.classList.remove('active');
        });

        // 添加当前活动状态
        if (activeLink) {
            activeLink.classList.add('active');

            // 如果是下拉菜单项，也激活父菜单
            const parentDropdown = activeLink.closest('.dropdown');
            if (parentDropdown) {
                const parentToggle = parentDropdown.querySelector('.dropdown-toggle');
                if (parentToggle) {
                    parentToggle.classList.add('active');
                }
            }
        }
    }

    /**
     * 拦截导航
     */
    interceptNavigation() {
        // 拦截所有可能的导航方式
        const originalPushState = history.pushState;
        const originalReplaceState = history.replaceState;

        history.pushState = (...args) => {
            originalPushState.apply(history, args);
            this.handleHistoryChange();
        };

        history.replaceState = (...args) => {
            originalReplaceState.apply(history, args);
            this.handleHistoryChange();
        };
    }

    /**
     * 处理历史记录变化
     */
    handleHistoryChange() {
        const path = window.location.pathname + window.location.search;
        if (path !== this.currentRoute) {
            this.loadRoute(path, false);
        }
    }

    /**
     * 处理初始路由
     */
    handleInitialRoute() {
        const currentPath = window.location.pathname + window.location.search;
        this.currentRoute = currentPath;

        // 如果是首页，不需要加载
        if (currentPath === '/' || currentPath === '/index') {
            console.log('🏠 当前在首页，无需加载');
            return;
        }

        // 加载当前页面
        this.loadRoute(currentPath, false);
    }

    /**
     * 显示错误信息
     */
    showError(message) {
        // 创建错误提示
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger alert-dismissible fade show';
        errorDiv.innerHTML = `
            <strong>错误：</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // 插入到内容区域顶部
        if (this.contentArea) {
            this.contentArea.insertBefore(errorDiv, this.contentArea.firstChild);
        }

        // 3秒后自动消失
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 3000);
    }

    /**
     * 显示用户提示
     */
    showUserTip() {
        setTimeout(() => {
            const tip = document.createElement('div');
            tip.className = 'alert alert-info alert-dismissible fade show position-fixed';
            tip.style.cssText = 'top: 20px; right: 20px; z-index: 1050; max-width: 300px;';
            tip.innerHTML = `
                <small>
                    <i class="fas fa-info-circle"></i>
                    SPA模式已启用，页面切换将更加流畅！
                </small>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;

            document.body.appendChild(tip);

            // 5秒后自动消失
            setTimeout(() => {
                if (tip.parentNode) {
                    tip.remove();
                }
            }, 5000);
        }, 1000);
    }

    /**
     * 判断是否应该拦截表单
     */
    shouldInterceptForm(form) {
        // 不拦截文件上传表单
        if (form.enctype === 'multipart/form-data') return false;

        // 不拦截外部提交的表单
        const action = form.action;
        if (action && (action.startsWith('http') || action.includes('://'))) return false;

        return true;
    }

    /**
     * 处理表单提交
     */
    async handleFormSubmit(form) {
        try {
            this.showLoading();

            const formData = new FormData(form);
            const method = form.method || 'POST';
            const action = form.action || window.location.pathname;

            const response = await fetch(action, {
                method: method,
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-SPA-Request': 'true'
                }
            });

            if (response.ok) {
                const html = await response.text();
                this.renderPage(html);
            } else {
                throw new Error(`表单提交失败: ${response.status}`);
            }

        } catch (error) {
            console.error('表单提交错误:', error);
            this.showError('表单提交失败，请重试');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * 清除缓存
     */
    clearCache() {
        this.pageCache.clear();
        console.log('🗑️ 页面缓存已清除');
    }

    /**
     * 获取当前路由
     */
    getCurrentRoute() {
        return this.currentRoute;
    }

    /**
     * 销毁路由系统
     */
    destroy() {
        this.routes.clear();
        this.pageCache.clear();

        if (this.loadingIndicator) {
            this.loadingIndicator.remove();
        }

        this.isInitialized = false;
        console.log('🔥 SPA路由系统已销毁');
    }
}

// 全局实例
window.spaRouter = null;

// 自动初始化
document.addEventListener('DOMContentLoaded', () => {
    if (!window.spaRouter) {
        window.spaRouter = new SPARouter();
        window.spaRouter.init();
    }
});

// 导出类
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SPARouter;
}
