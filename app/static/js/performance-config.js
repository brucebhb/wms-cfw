/**
 * 性能优化配置文件
 * 集中管理所有性能优化相关的配置和策略
 */

window.PerformanceConfig = {
    // 基础配置
    enabled: true,
    debug: true,
    
    // 性能阈值配置
    thresholds: {
        // 页面加载时间阈值 (毫秒)
        loadTime: {
            excellent: 1000,    // 优秀
            good: 2000,         // 良好
            acceptable: 3000,   // 可接受
            poor: 5000,         // 较差
            critical: 8000      // 严重
        },
        
        // 内存使用阈值 (MB)
        memory: {
            normal: 50,
            warning: 100,
            critical: 200
        },
        
        // DOM复杂度阈值
        domComplexity: {
            simple: 500,
            moderate: 1000,
            complex: 2000,
            heavy: 3000
        },
        
        // 资源加载时间阈值 (毫秒)
        resourceLoad: {
            fast: 500,
            normal: 1000,
            slow: 2000,
            critical: 5000
        }
    },
    
    // 自动修复配置
    autoFix: {
        enabled: true,
        checkInterval: 120000,  // 120秒检查一次（减少频率）
        
        // 修复策略开关
        strategies: {
            cleanupEventListeners: true,    // 清理事件监听器
            optimizeImages: true,           // 优化图片
            lazyLoadResources: true,        // 懒加载资源
            cleanupDOM: true,               // 清理DOM
            memoryCleanup: true,            // 内存清理
            resourceOptimization: true,     // 资源优化
            cssOptimization: false,         // CSS优化 - 已禁用
            scriptOptimization: true        // 脚本优化
        },
        
        // 修复触发条件
        triggers: {
            loadTimeExceeded: true,         // 加载时间超标
            memoryExceeded: true,           // 内存超标
            domComplexityHigh: true,        // DOM复杂度过高
            resourceErrorsHigh: true,       // 资源错误率过高
            userInactivity: false           // 用户不活跃时
        }
    },
    
    // 监控配置
    monitoring: {
        enabled: true,
        
        // 监控项目
        items: {
            pageLoad: true,                 // 页面加载
            resourceLoad: true,             // 资源加载
            memoryUsage: true,              // 内存使用
            domChanges: true,               // DOM变化
            userInteraction: true,          // 用户交互
            networkStatus: true,            // 网络状态
            errorTracking: true             // 错误跟踪
        },
        
        // 数据收集
        dataCollection: {
            maxEntries: 1000,               // 最大记录数
            retentionTime: 3600000,         // 数据保留时间 (1小时)
            batchSize: 50,                  // 批处理大小
            compressionEnabled: true        // 启用压缩
        }
    },
    
    // 优化策略配置
    optimization: {
        // 预加载策略
        preload: {
            enabled: true,
            criticalResources: [
                'bootstrap.min.css',
                'fontawesome.min.css',
                'jquery.min.js'
            ],
            prefetchOnHover: true,          // 鼠标悬停时预取
            prefetchOnIdle: true            // 空闲时预取
        },
        
        // 懒加载策略
        lazyLoad: {
            enabled: true,
            images: true,
            iframes: true,
            scripts: true,
            threshold: 100,                 // 提前加载距离 (px)
            rootMargin: '50px'
        },
        
        // 缓存策略
        cache: {
            enabled: true,
            localStorage: true,
            sessionStorage: true,
            indexedDB: false,
            maxSize: 10485760,              // 10MB
            ttl: 3600000                    // 1小时
        },
        
        // 压缩策略
        compression: {
            enabled: true,
            gzip: true,
            brotli: true,
            minifyHTML: false,
            minifyCSS: true,                // CSS压缩 - 重新启用（安全模式）
            minifyJS: false,                // JS压缩保持禁用
            safeMode: true,                 // 安全模式：只压缩空白字符，不删除重要样式
            preserveImportant: true,        // 保留!important声明
            preserveCustomProperties: true  // 保留CSS自定义属性
        }
    },
    
    // 用户体验配置
    userExperience: {
        // 加载指示器
        loadingIndicator: {
            enabled: true,
            showAfter: 500,                 // 500ms后显示
            minDuration: 1000,              // 最小显示时间
            style: 'spinner'                // spinner, progress, skeleton
        },
        
        // 错误处理
        errorHandling: {
            enabled: true,
            showUserFriendlyMessages: true,
            autoRetry: true,
            maxRetries: 3,
            retryDelay: 1000
        },
        
        // 性能提示
        performanceHints: {
            enabled: true,
            showSlowLoadingWarning: true,
            showMemoryWarning: true,
            showOptimizationSuggestions: true
        }
    },
    
    // 开发者工具配置
    devTools: {
        enabled: true,
        
        // 性能面板
        performancePanel: {
            enabled: true,
            hotkey: 'Ctrl+Shift+P',
            autoOpen: false,
            updateInterval: 5000
        },
        
        // 控制台日志
        console: {
            enabled: true,
            logLevel: 'info',               // debug, info, warn, error
            showTimestamps: true,
            groupLogs: true
        },
        
        // 性能标记
        performanceMarks: {
            enabled: true,
            autoMark: true,
            customMarks: []
        }
    },
    
    // 网络优化配置
    network: {
        // 连接优化
        connection: {
            preconnect: [
                'https://cdn.bootcdn.net',
                'https://fonts.googleapis.com'
            ],
            dnsPrefetch: [
                '//cdn.jsdelivr.net',
                '//unpkg.com'
            ]
        },
        
        // 资源优化
        resources: {
            combineCSS: false,              // CSS合并 - 已禁用
            combineJS: false,
            inlineSmallResources: true,
            smallResourceThreshold: 1024,   // 1KB
            useWebP: true,
            useAVIF: false
        }
    },
    
    // 移动端优化配置
    mobile: {
        enabled: true,
        
        // 触摸优化
        touch: {
            fastClick: true,
            touchDelay: 300
        },
        
        // 视口优化
        viewport: {
            optimizeForMobile: true,
            preventZoom: false,
            initialScale: 1.0
        },
        
        // 资源优化
        resources: {
            reducedQuality: true,
            smallerImages: true,
            fewerAnimations: true
        }
    },
    
    // 实验性功能
    experimental: {
        enabled: false,
        
        features: {
            serviceWorker: false,
            webAssembly: false,
            webWorkers: false,
            sharedArrayBuffer: false,
            offscreenCanvas: false
        }
    },
    
    // 获取当前配置
    getCurrentConfig() {
        return JSON.parse(JSON.stringify(this));
    },
    
    // 更新配置
    updateConfig(newConfig) {
        Object.assign(this, newConfig);
        this.saveToStorage();
        this.notifyConfigChange();
    },
    
    // 重置为默认配置
    resetToDefaults() {
        // 保存当前配置作为备份
        this.saveBackup();
        
        // 重新加载默认配置
        location.reload();
    },
    
    // 保存配置到本地存储
    saveToStorage() {
        try {
            const config = this.getCurrentConfig();
            localStorage.setItem('performanceConfig', JSON.stringify(config));
        } catch (error) {
            console.warn('保存性能配置失败:', error);
        }
    },
    
    // 从本地存储加载配置
    loadFromStorage() {
        try {
            const saved = localStorage.getItem('performanceConfig');
            if (saved) {
                const config = JSON.parse(saved);
                Object.assign(this, config);
                return true;
            }
        } catch (error) {
            console.warn('加载性能配置失败:', error);
        }
        return false;
    },
    
    // 保存配置备份
    saveBackup() {
        try {
            const config = this.getCurrentConfig();
            const backup = {
                config: config,
                timestamp: Date.now(),
                version: '1.0'
            };
            localStorage.setItem('performanceConfigBackup', JSON.stringify(backup));
        } catch (error) {
            console.warn('保存配置备份失败:', error);
        }
    },
    
    // 恢复配置备份
    restoreBackup() {
        try {
            const backup = localStorage.getItem('performanceConfigBackup');
            if (backup) {
                const data = JSON.parse(backup);
                Object.assign(this, data.config);
                this.saveToStorage();
                return true;
            }
        } catch (error) {
            console.warn('恢复配置备份失败:', error);
        }
        return false;
    },
    
    // 通知配置变更
    notifyConfigChange() {
        const event = new CustomEvent('performanceConfigChanged', {
            detail: this.getCurrentConfig()
        });
        document.dispatchEvent(event);
    },
    
    // 验证配置
    validateConfig() {
        const errors = [];
        
        // 验证阈值
        if (this.thresholds.loadTime.excellent >= this.thresholds.loadTime.good) {
            errors.push('加载时间阈值配置错误');
        }
        
        if (this.thresholds.memory.normal >= this.thresholds.memory.warning) {
            errors.push('内存阈值配置错误');
        }
        
        // 验证间隔时间
        if (this.autoFix.checkInterval < 5000) {
            errors.push('检查间隔时间过短，建议至少5秒');
        }
        
        return errors;
    },
    
    // 获取性能等级
    getPerformanceLevel(metric, value) {
        const thresholds = this.thresholds[metric];
        if (!thresholds) return 'unknown';
        
        if (metric === 'loadTime') {
            if (value <= thresholds.excellent) return 'excellent';
            if (value <= thresholds.good) return 'good';
            if (value <= thresholds.acceptable) return 'acceptable';
            if (value <= thresholds.poor) return 'poor';
            return 'critical';
        }
        
        if (metric === 'memory') {
            if (value <= thresholds.normal) return 'normal';
            if (value <= thresholds.warning) return 'warning';
            return 'critical';
        }
        
        if (metric === 'domComplexity') {
            if (value <= thresholds.simple) return 'simple';
            if (value <= thresholds.moderate) return 'moderate';
            if (value <= thresholds.complex) return 'complex';
            return 'heavy';
        }
        
        return 'unknown';
    }
};

// 初始化配置
document.addEventListener('DOMContentLoaded', () => {
    // 尝试从本地存储加载配置
    if (!window.PerformanceConfig.loadFromStorage()) {
        console.log('🔧 使用默认性能配置');
    } else {
        console.log('🔧 已加载保存的性能配置');
    }
    
    // 验证配置
    const errors = window.PerformanceConfig.validateConfig();
    if (errors.length > 0) {
        console.warn('⚠️ 性能配置验证失败:', errors);
    }
    
    console.log('✅ 性能配置已初始化');
});

// 导出配置
if (typeof module !== 'undefined' && module.exports) {
    module.exports = window.PerformanceConfig;
}
