/**
 * 异步数据预加载器
 * 智能预测用户需求，提前加载数据
 */

class AsyncDataPreloader {
    constructor() {
        this.preloadQueue = new Map();
        this.loadedData = new Map();
        this.userBehavior = {
            visitedPages: [],
            clickPatterns: [],
            timeSpent: {}
        };
        this.config = {
            maxConcurrentLoads: 3,
            preloadDelay: 1000, // 1秒后开始预加载
            priorityThreshold: 0.7 // 预测概率阈值
        };
        
        this.init();
    }
    
    init() {
        // 监听用户行为
        this.trackUserBehavior();
        
        // 页面加载完成后开始预加载
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(() => {
                this.startIntelligentPreload();
            }, this.config.preloadDelay);
        });
    }
    
    /**
     * 智能预加载 - 基于用户行为预测
     */
    startIntelligentPreload() {
        console.log('🧠 开始智能数据预加载...');
        
        // 预测用户可能访问的数据
        const predictions = this.predictUserNeeds();
        
        // 按优先级排序
        const sortedPredictions = predictions.sort((a, b) => b.priority - a.priority);
        
        // 预加载高优先级数据
        sortedPredictions.forEach((prediction, index) => {
            if (prediction.priority > this.config.priorityThreshold && 
                index < this.config.maxConcurrentLoads) {
                this.preloadData(prediction);
            }
        });
    }
    
    /**
     * 预测用户需求
     */
    predictUserNeeds() {
        const predictions = [];
        const currentPage = window.location.pathname;
        
        // 基于当前页面预测
        if (currentPage.includes('/dashboard')) {
            predictions.push(
                { url: '/reports/api/dashboard_data?period=week', priority: 0.9, type: 'dashboard' },
                { url: '/reports/api/inventory_overview', priority: 0.8, type: 'inventory' },
                { url: '/reports/api/realtime_stats', priority: 0.7, type: 'realtime' }
            );
        }
        
        if (currentPage.includes('/inventory')) {
            predictions.push(
                { url: '/inventory/api/list?page=2', priority: 0.8, type: 'pagination' },
                { url: '/inventory/api/stats', priority: 0.7, type: 'stats' }
            );
        }
        
        // 基于用户历史行为预测
        const behaviorPredictions = this.analyzeUserBehavior();
        predictions.push(...behaviorPredictions);
        
        return predictions;
    }
    
    /**
     * 分析用户行为模式
     */
    analyzeUserBehavior() {
        const predictions = [];
        const { visitedPages, clickPatterns } = this.userBehavior;
        
        // 分析页面访问模式
        if (visitedPages.length > 2) {
            const lastPages = visitedPages.slice(-3);
            
            // 如果用户经常从仪表板跳转到库存页面
            if (lastPages.includes('/dashboard') && lastPages.includes('/inventory')) {
                predictions.push({
                    url: '/inventory/api/list',
                    priority: 0.6,
                    type: 'behavior_pattern'
                });
            }
        }
        
        return predictions;
    }
    
    /**
     * 执行数据预加载
     */
    async preloadData(prediction) {
        const { url, type } = prediction;
        
        if (this.loadedData.has(url)) {
            console.log(`📦 数据已预加载: ${url}`);
            return;
        }
        
        if (this.preloadQueue.has(url)) {
            console.log(`⏳ 数据正在预加载: ${url}`);
            return;
        }
        
        console.log(`🚀 开始预加载: ${url} (类型: ${type})`);
        
        const loadPromise = this.fetchData(url, type);
        this.preloadQueue.set(url, loadPromise);
        
        try {
            const data = await loadPromise;
            this.loadedData.set(url, {
                data,
                timestamp: Date.now(),
                type
            });
            
            console.log(`✅ 预加载完成: ${url}`);
            
            // 触发预加载完成事件
            this.dispatchEvent('preloadComplete', { url, type, data });
            
        } catch (error) {
            console.warn(`❌ 预加载失败: ${url}`, error);
        } finally {
            this.preloadQueue.delete(url);
        }
    }
    
    /**
     * 获取预加载的数据
     */
    getPreloadedData(url) {
        const cached = this.loadedData.get(url);
        if (cached) {
            // 检查数据是否还新鲜（5分钟内）
            const age = Date.now() - cached.timestamp;
            if (age < 5 * 60 * 1000) {
                console.log(`⚡ 使用预加载数据: ${url}`);
                return cached.data;
            } else {
                // 数据过期，删除
                this.loadedData.delete(url);
            }
        }
        return null;
    }
    
    /**
     * 网络请求
     */
    async fetchData(url, type) {
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-Preload-Type': type
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return response.json();
    }
    
    /**
     * 跟踪用户行为
     */
    trackUserBehavior() {
        // 跟踪页面访问
        this.userBehavior.visitedPages.push(window.location.pathname);
        
        // 跟踪点击行为
        document.addEventListener('click', (event) => {
            const target = event.target;
            const clickInfo = {
                tag: target.tagName,
                className: target.className,
                id: target.id,
                timestamp: Date.now()
            };
            
            this.userBehavior.clickPatterns.push(clickInfo);
            
            // 只保留最近50次点击
            if (this.userBehavior.clickPatterns.length > 50) {
                this.userBehavior.clickPatterns.shift();
            }
        });
        
        // 跟踪页面停留时间
        const startTime = Date.now();
        window.addEventListener('beforeunload', () => {
            const timeSpent = Date.now() - startTime;
            this.userBehavior.timeSpent[window.location.pathname] = timeSpent;
        });
    }
    
    /**
     * 事件分发
     */
    dispatchEvent(type, detail) {
        const event = new CustomEvent(`preloader:${type}`, { detail });
        document.dispatchEvent(event);
    }
    
    /**
     * 清理过期数据
     */
    cleanup() {
        const now = Date.now();
        const maxAge = 10 * 60 * 1000; // 10分钟
        
        for (const [url, cached] of this.loadedData.entries()) {
            if (now - cached.timestamp > maxAge) {
                this.loadedData.delete(url);
                console.log(`🗑️ 清理过期预加载数据: ${url}`);
            }
        }
    }
    
    /**
     * 获取统计信息
     */
    getStats() {
        return {
            preloadedItems: this.loadedData.size,
            queuedItems: this.preloadQueue.size,
            behaviorData: {
                visitedPages: this.userBehavior.visitedPages.length,
                clickPatterns: this.userBehavior.clickPatterns.length
            }
        };
    }
}

// 全局实例
window.asyncDataPreloader = new AsyncDataPreloader();

// 定期清理
setInterval(() => {
    window.asyncDataPreloader.cleanup();
}, 5 * 60 * 1000); // 每5分钟清理一次
