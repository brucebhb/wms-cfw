/**
 * 仪表板缓存优化器
 * 配合后端双层缓存系统，提供前端优化
 */

class DashboardCacheOptimizer {
    constructor() {
        this.cache = new Map();
        this.loadingStates = new Map();
        this.refreshIntervals = new Map();
        this.config = {
            // 缓存配置
            maxCacheSize: 50,
            defaultTTL: 5 * 60 * 1000, // 5分钟
            
            // 刷新间隔配置
            refreshIntervals: {
                realtime: 30 * 1000,    // 30秒
                dashboard: 5 * 60 * 1000, // 5分钟
                inventory: 10 * 60 * 1000, // 10分钟
                historical: 30 * 60 * 1000  // 30分钟
            },
            
            // 重试配置
            maxRetries: 3,
            retryDelay: 1000
        };
        
        this.init();
    }
    
    init() {
        console.log('🚀 仪表板缓存优化器已启动');
        
        // 监听页面可见性变化
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseRefresh();
            } else {
                this.resumeRefresh();
            }
        });
        
        // 监听网络状态变化
        if ('connection' in navigator) {
            navigator.connection.addEventListener('change', () => {
                this.handleNetworkChange();
            });
        }
        
        // 页面卸载时清理
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
    }
    
    /**
     * 获取数据（带缓存）
     */
    async getData(key, url, options = {}) {
        const cacheKey = this.generateCacheKey(key, options);
        
        // 检查本地缓存
        const cached = this.getFromCache(cacheKey);
        if (cached && !this.isExpired(cached)) {
            console.log(`📦 缓存命中: ${key}`);
            return cached.data;
        }
        
        // 检查是否正在加载
        if (this.loadingStates.has(cacheKey)) {
            console.log(`⏳ 等待加载: ${key}`);
            return this.loadingStates.get(cacheKey);
        }
        
        // 发起请求
        const loadingPromise = this.fetchData(url, options, key);
        this.loadingStates.set(cacheKey, loadingPromise);
        
        try {
            const data = await loadingPromise;
            
            // 存储到缓存
            this.setCache(cacheKey, data, options.ttl || this.config.defaultTTL);
            
            return data;
        } finally {
            this.loadingStates.delete(cacheKey);
        }
    }
    
    /**
     * 发起网络请求
     */
    async fetchData(url, options, key) {
        const startTime = Date.now();
        let retries = 0;
        
        while (retries < this.config.maxRetries) {
            try {
                console.log(`🌐 请求数据: ${key} (尝试 ${retries + 1})`);
                
                const response = await fetch(url, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest',
                        ...options.headers
                    },
                    ...options
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                const duration = Date.now() - startTime;
                
                console.log(`✅ 数据获取成功: ${key} (${duration}ms)`);
                
                // 触发成功事件
                this.dispatchEvent('dataLoaded', { key, data, duration });
                
                return data;
                
            } catch (error) {
                retries++;
                console.warn(`❌ 请求失败: ${key} (尝试 ${retries}/${this.config.maxRetries})`, error);
                
                if (retries >= this.config.maxRetries) {
                    // 触发错误事件
                    this.dispatchEvent('dataError', { key, error });
                    throw error;
                }
                
                // 等待后重试
                await this.delay(this.config.retryDelay * retries);
            }
        }
    }
    
    /**
     * 设置自动刷新
     */
    setAutoRefresh(key, url, options = {}) {
        const interval = options.interval || this.config.refreshIntervals.dashboard;
        
        // 清除现有定时器
        if (this.refreshIntervals.has(key)) {
            clearInterval(this.refreshIntervals.get(key));
        }
        
        // 设置新定时器
        const intervalId = setInterval(async () => {
            try {
                console.log(`🔄 自动刷新: ${key}`);
                await this.refreshData(key, url, options);
            } catch (error) {
                console.error(`自动刷新失败: ${key}`, error);
            }
        }, interval);
        
        this.refreshIntervals.set(key, intervalId);
        console.log(`⏰ 自动刷新已设置: ${key} (${interval/1000}秒)`);
    }
    
    /**
     * 刷新数据
     */
    async refreshData(key, url, options = {}) {
        const cacheKey = this.generateCacheKey(key, options);
        
        // 删除缓存
        this.cache.delete(cacheKey);
        
        // 重新获取数据
        return this.getData(key, url, options);
    }
    
    /**
     * 预加载数据
     */
    async preloadData(items) {
        console.log(`🔥 开始预加载 ${items.length} 项数据`);
        
        const promises = items.map(async (item) => {
            try {
                await this.getData(item.key, item.url, item.options);
                console.log(`✅ 预加载完成: ${item.key}`);
            } catch (error) {
                console.warn(`❌ 预加载失败: ${item.key}`, error);
            }
        });
        
        await Promise.allSettled(promises);
        console.log('🎉 预加载完成');
    }
    
    /**
     * 缓存管理
     */
    generateCacheKey(key, options) {
        const params = options.params ? JSON.stringify(options.params) : '';
        return `${key}:${params}`;
    }
    
    getFromCache(key) {
        return this.cache.get(key);
    }
    
    setCache(key, data, ttl) {
        // 检查缓存大小
        if (this.cache.size >= this.config.maxCacheSize) {
            this.evictOldest();
        }
        
        this.cache.set(key, {
            data,
            timestamp: Date.now(),
            ttl
        });
    }
    
    isExpired(cached) {
        return Date.now() - cached.timestamp > cached.ttl;
    }
    
    evictOldest() {
        const oldest = Array.from(this.cache.entries())
            .sort((a, b) => a[1].timestamp - b[1].timestamp)[0];
        
        if (oldest) {
            this.cache.delete(oldest[0]);
            console.log(`🗑️ 清理过期缓存: ${oldest[0]}`);
        }
    }
    
    /**
     * 生命周期管理
     */
    pauseRefresh() {
        console.log('⏸️ 暂停自动刷新');
        this.refreshIntervals.forEach((intervalId) => {
            clearInterval(intervalId);
        });
    }
    
    resumeRefresh() {
        console.log('▶️ 恢复自动刷新');
        // 重新设置定时器需要外部调用 setAutoRefresh
    }
    
    cleanup() {
        console.log('🧹 清理缓存优化器');
        
        // 清理定时器
        this.refreshIntervals.forEach((intervalId) => {
            clearInterval(intervalId);
        });
        this.refreshIntervals.clear();
        
        // 清理缓存
        this.cache.clear();
        
        // 清理加载状态
        this.loadingStates.clear();
    }
    
    /**
     * 网络状态处理
     */
    handleNetworkChange() {
        const connection = navigator.connection;
        if (connection) {
            console.log(`📶 网络状态变化: ${connection.effectiveType}`);
            
            // 根据网络状态调整策略
            if (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g') {
                // 慢网络：增加缓存时间，减少刷新频率
                this.config.defaultTTL = 10 * 60 * 1000; // 10分钟
            } else {
                // 快网络：恢复默认设置
                this.config.defaultTTL = 5 * 60 * 1000; // 5分钟
            }
        }
    }
    
    /**
     * 事件系统
     */
    dispatchEvent(type, detail) {
        const event = new CustomEvent(`dashboardCache:${type}`, { detail });
        document.dispatchEvent(event);
    }
    
    /**
     * 工具方法
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    /**
     * 获取缓存统计
     */
    getStats() {
        const stats = {
            cacheSize: this.cache.size,
            maxCacheSize: this.config.maxCacheSize,
            activeRefreshers: this.refreshIntervals.size,
            loadingRequests: this.loadingStates.size
        };
        
        // 计算命中率（简化版）
        const cacheEntries = Array.from(this.cache.values());
        const validEntries = cacheEntries.filter(entry => !this.isExpired(entry));
        stats.hitRate = cacheEntries.length > 0 ? (validEntries.length / cacheEntries.length * 100).toFixed(1) : 0;
        
        return stats;
    }
}

// 全局实例
window.dashboardCacheOptimizer = new DashboardCacheOptimizer();

// 导出给其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardCacheOptimizer;
}
