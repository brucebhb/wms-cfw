/**
 * 页面加载优化器
 * 解决页面跳转卡住问题
 */

(function() {
    'use strict';

    class PageLoadOptimizer {
        constructor() {
            this.isLoading = false;
            this.loadingTimeout = null;
            this.eventListeners = new Map();
            this.init();
        }

        init() {
            this.setupLoadingIndicator();
            this.setupNavigationOptimization();
            this.setupErrorHandler();
            this.setupPerformanceMonitoring();
            this.cleanupOnUnload();
        }

        /**
         * 设置加载指示器
         */
        setupLoadingIndicator() {
            // 监听页面跳转
            document.addEventListener('click', (e) => {
                const link = e.target.closest('a');
                if (link && this.shouldShowLoading(link)) {
                    this.showLoading();
                }
            });

            // 监听表单提交
            document.addEventListener('submit', (e) => {
                if (e.target.tagName === 'FORM') {
                    this.showLoading();
                }
            });
        }

        /**
         * 判断是否应该显示加载指示器
         */
        shouldShowLoading(link) {
            const href = link.getAttribute('href');
            if (!href || href.startsWith('#') || href.startsWith('javascript:')) {
                return false;
            }
            
            // 排除外部链接
            if (href.startsWith('http') && !href.includes(window.location.hostname)) {
                return false;
            }
            
            // 排除下载链接
            if (link.hasAttribute('download')) {
                return false;
            }
            
            return true;
        }

        /**
         * 显示加载状态
         */
        showLoading() {
            if (this.isLoading) return;
            
            this.isLoading = true;
            
            // 创建加载指示器
            this.createLoadingIndicator();
            
            // 设置超时处理
            this.loadingTimeout = setTimeout(() => {
                this.showTimeoutError();
            }, 15000); // 15秒超时
        }

        /**
         * 创建加载指示器
         */
        createLoadingIndicator() {
            // 移除现有的加载指示器
            this.removeLoadingIndicator();
            
            const loader = document.createElement('div');
            loader.id = 'page-load-indicator';
            loader.innerHTML = `
                <div style="
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 4px;
                    background: linear-gradient(90deg, #007bff 0%, #28a745 50%, #007bff 100%);
                    background-size: 200% 100%;
                    animation: loading-progress 2s infinite;
                    z-index: 10001;
                "></div>
                <div style="
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: rgba(0, 123, 255, 0.9);
                    color: white;
                    padding: 10px 15px;
                    border-radius: 5px;
                    font-size: 14px;
                    z-index: 10002;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                ">
                    <i class="fas fa-spinner fa-spin me-2"></i>页面加载中...
                </div>
            `;
            
            // 添加CSS动画
            if (!document.getElementById('loading-animation-style')) {
                const style = document.createElement('style');
                style.id = 'loading-animation-style';
                style.textContent = `
                    @keyframes loading-progress {
                        0% { background-position: -200% 0; }
                        100% { background-position: 200% 0; }
                    }
                `;
                document.head.appendChild(style);
            }
            
            document.body.appendChild(loader);
        }

        /**
         * 移除加载指示器
         */
        removeLoadingIndicator() {
            const loader = document.getElementById('page-load-indicator');
            if (loader) {
                loader.remove();
            }
        }

        /**
         * 隐藏加载状态
         */
        hideLoading() {
            this.isLoading = false;
            this.removeLoadingIndicator();
            
            if (this.loadingTimeout) {
                clearTimeout(this.loadingTimeout);
                this.loadingTimeout = null;
            }
        }

        /**
         * 显示超时错误
         */
        showTimeoutError() {
            this.removeLoadingIndicator();
            
            const errorDiv = document.createElement('div');
            errorDiv.id = 'page-load-timeout';
            errorDiv.innerHTML = `
                <div style="
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                    z-index: 10003;
                    text-align: center;
                    max-width: 400px;
                ">
                    <i class="fas fa-exclamation-triangle text-warning" style="font-size: 48px; margin-bottom: 15px;"></i>
                    <h5>页面加载超时</h5>
                    <p class="text-muted">页面加载时间过长，可能是网络问题或服务器繁忙。</p>
                    <div class="mt-3">
                        <button class="btn btn-primary me-2" onclick="location.reload()">
                            <i class="fas fa-refresh me-1"></i>重新加载
                        </button>
                        <button class="btn btn-secondary" onclick="history.back()">
                            <i class="fas fa-arrow-left me-1"></i>返回上页
                        </button>
                    </div>
                </div>
                <div style="
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0,0,0,0.5);
                    z-index: 10002;
                " onclick="this.parentElement.remove()"></div>
            `;
            
            document.body.appendChild(errorDiv);
            
            // 10秒后自动移除
            setTimeout(() => {
                if (document.getElementById('page-load-timeout')) {
                    errorDiv.remove();
                }
            }, 10000);
            
            this.isLoading = false;
        }

        /**
         * 设置导航优化
         */
        setupNavigationOptimization() {
            // 启用智能预加载功能
            this.preloadImportantPages();

            // 优化链接点击
            this.optimizeLinkClicks();
        }

        /**
         * 预加载重要页面
         */
        preloadImportantPages() {
            // 智能预加载重要页面，只预加载确实存在的页面
            // 根据用户权限和仓库类型动态配置
            const importantLinks = this.getImportantLinksForCurrentUser();

            // 只预加载存在的页面
            importantLinks.forEach(url => {
                // 先检查URL是否有效
                fetch(url, { method: 'HEAD' })
                    .then(response => {
                        if (response.ok) {
                            const link = document.createElement('link');
                            link.rel = 'prefetch';
                            link.href = url;
                            document.head.appendChild(link);
                            console.log(`预加载页面: ${url}`);
                        }
                    })
                    .catch(error => {
                        console.warn(`预加载失败: ${url}`, error);
                    });
            });
        }

        /**
         * 根据当前用户获取重要链接
         */
        getImportantLinksForCurrentUser() {
            const links = [];

            // 基于当前页面路径判断用户可能访问的页面
            const currentPath = window.location.pathname;

            if (currentPath.includes('/frontend/')) {
                // 前端仓用户可能访问的页面
                links.push(
                    '/frontend/inbound/integrated',
                    '/frontend/outbound/list',
                    '/frontend/inventory/list'
                );
            } else if (currentPath.includes('/backend/')) {
                // 后端仓用户可能访问的页面
                links.push(
                    '/backend/inbound/direct',
                    '/backend/outbound/list',
                    '/backend/inventory/list'
                );
            } else if (currentPath.includes('/admin/')) {
                // 管理员可能访问的页面
                links.push(
                    '/admin/users',
                    '/admin/warehouses',
                    '/admin/audit_logs'
                );
            }

            // 通用页面（所有用户都可能访问）
            links.push('/reports/dashboard');

            return links;
        }

        /**
         * 优化链接点击
         */
        optimizeLinkClicks() {
            // 防止重复点击
            document.addEventListener('click', (e) => {
                const link = e.target.closest('a');
                if (link && this.shouldShowLoading(link)) {
                    // 防止重复点击
                    if (link.dataset.clicked === 'true') {
                        e.preventDefault();
                        return;
                    }
                    
                    link.dataset.clicked = 'true';
                    
                    // 3秒后重置
                    setTimeout(() => {
                        link.dataset.clicked = 'false';
                    }, 3000);
                }
            });
        }

        /**
         * 设置错误处理
         */
        setupErrorHandler() {
            window.addEventListener('error', (e) => {
                console.error('页面错误:', e.error);
                this.hideLoading();
            });
            
            window.addEventListener('unhandledrejection', (e) => {
                console.error('未处理的Promise拒绝:', e.reason);
                this.hideLoading();
            });
        }

        /**
         * 设置性能监控
         */
        setupPerformanceMonitoring() {
            window.addEventListener('load', () => {
                const loadTime = performance.now();
                console.log(`页面加载时间: ${loadTime.toFixed(2)}ms`);
                
                if (loadTime > 5000) {
                    console.warn('页面加载较慢，建议优化');
                }
                
                this.hideLoading();
            });
        }

        /**
         * 页面卸载时清理
         */
        cleanupOnUnload() {
            window.addEventListener('beforeunload', () => {
                this.cleanup();
            });
        }

        /**
         * 清理资源
         */
        cleanup() {
            this.hideLoading();
            this.eventListeners.clear();
            
            // 清理预加载的资源
            const prefetchLinks = document.querySelectorAll('link[rel="prefetch"]');
            prefetchLinks.forEach(link => link.remove());
        }
    }

    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.pageLoadOptimizer = new PageLoadOptimizer();
        });
    } else {
        window.pageLoadOptimizer = new PageLoadOptimizer();
    }

    // 导出到全局
    window.PageLoadOptimizer = PageLoadOptimizer;

})();
