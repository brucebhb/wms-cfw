/**
 * 懒加载和骨架屏管理器
 * 实现智能的内容懒加载和优雅的加载状态
 */

class LazyLoader {
    constructor() {
        this.observers = new Map();
        this.loadingStates = new Map();
        this.config = {
            rootMargin: '50px', // 提前50px开始加载
            threshold: 0.1,     // 10%可见时触发
            skeletonDuration: 300 // 骨架屏最小显示时间
        };
        
        this.init();
    }
    
    init() {
        // 创建Intersection Observer
        this.createObserver();
        
        // 自动检测页面中的懒加载元素
        this.autoDetectLazyElements();
        
        console.log('💀 懒加载管理器已初始化');
    }
    
    /**
     * 创建Intersection Observer
     */
    createObserver() {
        if ('IntersectionObserver' in window) {
            this.observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.loadElement(entry.target);
                        this.observer.unobserve(entry.target);
                    }
                });
            }, {
                rootMargin: this.config.rootMargin,
                threshold: this.config.threshold
            });
        } else {
            // 降级处理：不支持IntersectionObserver时立即加载
            console.warn('浏览器不支持IntersectionObserver，使用降级方案');
        }
    }
    
    /**
     * 自动检测懒加载元素
     */
    autoDetectLazyElements() {
        // 检测带有data-lazy属性的元素
        const lazyElements = document.querySelectorAll('[data-lazy]');
        
        lazyElements.forEach(element => {
            this.registerLazyElement(element);
        });
        
        console.log(`🔍 检测到 ${lazyElements.length} 个懒加载元素`);
    }
    
    /**
     * 注册懒加载元素
     */
    registerLazyElement(element) {
        const lazyType = element.dataset.lazy;
        const lazyUrl = element.dataset.lazyUrl;
        const lazyTarget = element.dataset.lazyTarget || element;
        
        // 显示骨架屏
        this.showSkeleton(element, lazyType);
        
        // 添加到观察器
        if (this.observer) {
            this.observer.observe(element);
        } else {
            // 降级：立即加载
            setTimeout(() => this.loadElement(element), 100);
        }
    }
    
    /**
     * 显示骨架屏
     */
    showSkeleton(element, type) {
        const skeletonHtml = this.generateSkeleton(type);
        
        // 保存原始内容
        if (!element.dataset.originalContent) {
            element.dataset.originalContent = element.innerHTML;
        }
        
        // 显示骨架屏
        element.innerHTML = skeletonHtml;
        element.classList.add('skeleton-loading');
        
        console.log(`💀 显示骨架屏: ${type}`);
    }
    
    /**
     * 生成骨架屏HTML
     */
    generateSkeleton(type) {
        const skeletons = {
            'dashboard-card': `
                <div class="skeleton-card">
                    <div class="skeleton-header">
                        <div class="skeleton-line skeleton-title"></div>
                        <div class="skeleton-line skeleton-subtitle"></div>
                    </div>
                    <div class="skeleton-content">
                        <div class="skeleton-number"></div>
                        <div class="skeleton-chart"></div>
                    </div>
                </div>
            `,
            
            'data-table': `
                <div class="skeleton-table">
                    <div class="skeleton-table-header">
                        ${Array(5).fill('<div class="skeleton-line skeleton-th"></div>').join('')}
                    </div>
                    <div class="skeleton-table-body">
                        ${Array(8).fill(`
                            <div class="skeleton-table-row">
                                ${Array(5).fill('<div class="skeleton-line skeleton-td"></div>').join('')}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `,
            
            'chart': `
                <div class="skeleton-chart-container">
                    <div class="skeleton-chart-title"></div>
                    <div class="skeleton-chart-area">
                        <div class="skeleton-bars">
                            ${Array(7).fill('<div class="skeleton-bar"></div>').join('')}
                        </div>
                        <div class="skeleton-axis-x"></div>
                        <div class="skeleton-axis-y"></div>
                    </div>
                </div>
            `,
            
            'list': `
                <div class="skeleton-list">
                    ${Array(6).fill(`
                        <div class="skeleton-list-item">
                            <div class="skeleton-avatar"></div>
                            <div class="skeleton-content">
                                <div class="skeleton-line skeleton-name"></div>
                                <div class="skeleton-line skeleton-desc"></div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `,
            
            'default': `
                <div class="skeleton-default">
                    <div class="skeleton-line skeleton-title"></div>
                    <div class="skeleton-line skeleton-content"></div>
                    <div class="skeleton-line skeleton-content short"></div>
                </div>
            `
        };
        
        return skeletons[type] || skeletons['default'];
    }
    
    /**
     * 加载元素内容
     */
    async loadElement(element) {
        const lazyType = element.dataset.lazy;
        const lazyUrl = element.dataset.lazyUrl;
        const loadingKey = this.generateLoadingKey(element);
        
        // 防止重复加载
        if (this.loadingStates.has(loadingKey)) {
            return;
        }
        
        this.loadingStates.set(loadingKey, true);
        const startTime = Date.now();
        
        try {
            console.log(`🚀 开始懒加载: ${lazyType} - ${lazyUrl}`);
            
            let content;
            
            if (lazyUrl) {
                // 从URL加载数据
                content = await this.fetchContent(lazyUrl, lazyType);
            } else {
                // 从预加载数据获取
                content = await this.getPreloadedContent(element);
            }
            
            // 确保骨架屏至少显示配置的最小时间
            const elapsed = Date.now() - startTime;
            const remainingTime = Math.max(0, this.config.skeletonDuration - elapsed);
            
            if (remainingTime > 0) {
                await this.delay(remainingTime);
            }
            
            // 渲染内容
            await this.renderContent(element, content, lazyType);
            
            console.log(`✅ 懒加载完成: ${lazyType}`);
            
            // 触发加载完成事件
            this.dispatchEvent('lazyLoadComplete', {
                element,
                type: lazyType,
                duration: Date.now() - startTime
            });
            
        } catch (error) {
            console.error(`❌ 懒加载失败: ${lazyType}`, error);
            this.showError(element, error);
        } finally {
            this.loadingStates.delete(loadingKey);
        }
    }
    
    /**
     * 获取内容
     */
    async fetchContent(url, type) {
        // 首先尝试从预加载器获取
        if (window.asyncDataPreloader) {
            const preloadedData = window.asyncDataPreloader.getPreloadedData(url);
            if (preloadedData) {
                return preloadedData;
            }
        }
        
        // 发起网络请求
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-Lazy-Type': type
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return response.json();
    }
    
    /**
     * 获取预加载内容
     */
    async getPreloadedContent(element) {
        // 模拟异步操作
        await this.delay(200);
        
        // 返回原始内容或生成内容
        return {
            html: element.dataset.originalContent || '<p>内容已加载</p>'
        };
    }
    
    /**
     * 渲染内容
     */
    async renderContent(element, content, type) {
        // 移除骨架屏样式
        element.classList.remove('skeleton-loading');
        
        // 添加淡入动画
        element.style.opacity = '0';
        element.style.transition = 'opacity 0.3s ease-in-out';
        
        // 根据类型渲染内容
        if (content.html) {
            element.innerHTML = content.html;
        } else if (content.data) {
            element.innerHTML = this.renderData(content.data, type);
        } else {
            element.innerHTML = element.dataset.originalContent || '';
        }
        
        // 触发淡入动画
        requestAnimationFrame(() => {
            element.style.opacity = '1';
        });
        
        // 初始化新加载的内容
        this.initializeLoadedContent(element, type);
    }
    
    /**
     * 渲染数据为HTML
     */
    renderData(data, type) {
        switch (type) {
            case 'dashboard-card':
                return this.renderDashboardCard(data);
            case 'data-table':
                return this.renderDataTable(data);
            case 'chart':
                return this.renderChart(data);
            case 'list':
                return this.renderList(data);
            default:
                return JSON.stringify(data);
        }
    }
    
    /**
     * 渲染仪表板卡片
     */
    renderDashboardCard(data) {
        return `
            <div class="dashboard-card">
                <div class="card-header">
                    <h3>${data.title || '数据卡片'}</h3>
                    <span class="card-subtitle">${data.subtitle || ''}</span>
                </div>
                <div class="card-content">
                    <div class="card-number">${data.value || 0}</div>
                    <div class="card-trend ${data.trend || 'neutral'}">
                        ${data.change || '0%'}
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * 渲染数据表格
     */
    renderDataTable(data) {
        const headers = data.headers || [];
        const rows = data.rows || [];
        
        return `
            <div class="data-table">
                <table class="table">
                    <thead>
                        <tr>
                            ${headers.map(header => `<th>${header}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${rows.map(row => `
                            <tr>
                                ${row.map(cell => `<td>${cell}</td>`).join('')}
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }
    
    /**
     * 初始化加载的内容
     */
    initializeLoadedContent(element, type) {
        // 根据类型执行特定的初始化
        switch (type) {
            case 'chart':
                this.initializeChart(element);
                break;
            case 'data-table':
                this.initializeTable(element);
                break;
        }
        
        // 重新检测新的懒加载元素
        const newLazyElements = element.querySelectorAll('[data-lazy]');
        newLazyElements.forEach(el => this.registerLazyElement(el));
    }
    
    /**
     * 显示错误状态
     */
    showError(element, error) {
        element.classList.remove('skeleton-loading');
        element.innerHTML = `
            <div class="lazy-load-error">
                <div class="error-icon">⚠️</div>
                <div class="error-message">加载失败</div>
                <button class="retry-btn" onclick="window.lazyLoader.retryLoad('${this.generateLoadingKey(element)}')">
                    重试
                </button>
            </div>
        `;
    }
    
    /**
     * 重试加载
     */
    retryLoad(loadingKey) {
        // 实现重试逻辑
        console.log(`🔄 重试加载: ${loadingKey}`);
    }
    
    /**
     * 工具方法
     */
    generateLoadingKey(element) {
        return element.dataset.lazyUrl || element.id || Math.random().toString(36);
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    dispatchEvent(type, detail) {
        const event = new CustomEvent(`lazyLoader:${type}`, { detail });
        document.dispatchEvent(event);
    }
    
    initializeChart(element) {
        // 图表初始化逻辑
        console.log('📊 初始化图表');
    }
    
    initializeTable(element) {
        // 表格初始化逻辑
        console.log('📋 初始化表格');
    }
}

// 全局实例
window.lazyLoader = new LazyLoader();
