/**
 * 性能优化器管理器
 * 统一管理所有性能优化器，避免冲突和重复
 */

class PerformanceOptimizerManager {
    constructor() {
        this.optimizers = new Map();
        this.isInitialized = false;
        this.config = {
            maxOptimizers: 3, // 最多同时运行3个优化器
            debugMode: false,
            enableConflictDetection: true
        };
        
        this.init();
    }
    
    init() {
        if (this.isInitialized) {
            console.warn('⚠️ 性能优化器管理器已初始化，跳过重复初始化');
            return;
        }
        
        console.log('🎛️ 性能优化器管理器启动');
        
        // 检测现有的优化器
        this.detectExistingOptimizers();
        
        // 设置冲突检测
        if (this.config.enableConflictDetection) {
            this.setupConflictDetection();
        }
        
        // 优化器优先级管理
        this.setupPriorityManagement();
        
        this.isInitialized = true;
        
        // 提供全局控制接口
        window.performanceOptimizerManager = this;
    }
    
    // 检测现有的优化器
    detectExistingOptimizers() {
        const potentialOptimizers = [
            { name: 'autoPerformanceFixer', instance: window.autoPerformanceFixer },
            { name: 'safePerformanceOptimizer', instance: window.safePerformanceOptimizer },
            { name: 'integratedPM', instance: window.integratedPM },
            { name: 'performanceDashboard', instance: window.performanceDashboard },
            { name: 'unifiedPerformanceManager', instance: window.unifiedPerformanceManager }
        ];
        
        let activeCount = 0;
        potentialOptimizers.forEach(optimizer => {
            if (optimizer.instance) {
                this.optimizers.set(optimizer.name, {
                    instance: optimizer.instance,
                    priority: this.getOptimizerPriority(optimizer.name),
                    active: true
                });
                activeCount++;
                console.log(`✅ 检测到优化器: ${optimizer.name}`);
            }
        });
        
        console.log(`📊 检测到 ${activeCount} 个活跃的性能优化器`);
        
        if (activeCount > this.config.maxOptimizers) {
            console.warn(`⚠️ 优化器数量过多 (${activeCount}/${this.config.maxOptimizers})，可能影响性能`);
            this.optimizeOptimizerCount();
        }
    }
    
    // 获取优化器优先级
    getOptimizerPriority(name) {
        const priorities = {
            'integratedPM': 1,           // 最高优先级
            'safePerformanceOptimizer': 2,
            'autoPerformanceFixer': 3,
            'unifiedPerformanceManager': 4,
            'performanceDashboard': 5     // 最低优先级
        };
        
        return priorities[name] || 10;
    }
    
    // 优化优化器数量
    optimizeOptimizerCount() {
        console.log('🔧 开始优化优化器数量...');
        
        // 按优先级排序
        const sortedOptimizers = Array.from(this.optimizers.entries())
            .sort((a, b) => a[1].priority - b[1].priority);
        
        // 保留高优先级的优化器，禁用低优先级的
        for (let i = this.config.maxOptimizers; i < sortedOptimizers.length; i++) {
            const [name, optimizer] = sortedOptimizers[i];
            this.disableOptimizer(name);
        }
    }
    
    // 禁用优化器
    disableOptimizer(name) {
        const optimizer = this.optimizers.get(name);
        if (optimizer && optimizer.active) {
            try {
                // 尝试调用优化器的禁用方法
                if (optimizer.instance.disable) {
                    optimizer.instance.disable();
                } else if (optimizer.instance.destroy) {
                    optimizer.instance.destroy();
                } else if (optimizer.instance.cleanup) {
                    optimizer.instance.cleanup();
                }
                
                optimizer.active = false;
                console.log(`⏸️ 已禁用优化器: ${name}`);
                
            } catch (error) {
                console.warn(`⚠️ 禁用优化器 ${name} 时出错:`, error);
            }
        }
    }
    
    // 设置冲突检测
    setupConflictDetection() {
        console.log('🔍 设置优化器冲突检测...');
        
        // 检测重复的定时器
        this.detectTimerConflicts();
        
        // 检测重复的事件监听器
        this.detectEventConflicts();
        
        // 检测重复的DOM操作
        this.detectDOMConflicts();
    }
    
    // 检测定时器冲突
    detectTimerConflicts() {
        const originalSetInterval = window.setInterval;
        const activeIntervals = new Set();
        
        window.setInterval = function(callback, delay, ...args) {
            const intervalId = originalSetInterval.call(this, callback, delay, ...args);
            activeIntervals.add(intervalId);
            
            // 检测是否有过多的短间隔定时器
            if (delay < 5000 && activeIntervals.size > 5) {
                console.warn(`⚠️ 检测到过多的短间隔定时器 (${activeIntervals.size}个)，可能影响性能`);
            }
            
            return intervalId;
        };
        
        const originalClearInterval = window.clearInterval;
        window.clearInterval = function(intervalId) {
            activeIntervals.delete(intervalId);
            return originalClearInterval.call(this, intervalId);
        };
    }
    
    // 检测事件冲突
    detectEventConflicts() {
        const eventCounts = new Map();
        const originalAddEventListener = EventTarget.prototype.addEventListener;
        const manager = this; // 保存管理器实例的引用

        EventTarget.prototype.addEventListener = function(type, listener, options) {
            const count = eventCounts.get(type) || 0;
            eventCounts.set(type, count + 1);

            // 检测是否有过多的相同类型事件监听器
            // 对于复杂页面（如货量报表），适当提高阈值
            const threshold = manager.isComplexPage() ? 25 : 15;
            if (count > threshold) {
                console.warn(`⚠️ 检测到过多的 ${type} 事件监听器 (${count}个，阈值: ${threshold})`);
            }

            return originalAddEventListener.call(this, type, listener, options);
        };
    }
    
    // 检测DOM操作冲突
    detectDOMConflicts() {
        const domOperations = new Map();
        
        // 监控样式添加
        const originalAppendChild = Node.prototype.appendChild;
        Node.prototype.appendChild = function(child) {
            if (child.tagName === 'STYLE') {
                const count = domOperations.get('style') || 0;
                domOperations.set('style', count + 1);
                
                if (count > 5) {
                    console.warn(`⚠️ 检测到过多的样式元素添加 (${count}个)`);
                }
            }
            
            return originalAppendChild.call(this, child);
        };
    }
    
    // 设置优先级管理
    setupPriorityManagement() {
        console.log('📋 设置优化器优先级管理...');
        
        // 定期检查优化器状态
        setInterval(() => {
            this.checkOptimizerHealth();
        }, 60000); // 每分钟检查一次
    }
    
    // 检查优化器健康状态
    checkOptimizerHealth() {
        if (!this.config.debugMode) return;
        
        console.log('🏥 检查优化器健康状态...');
        
        this.optimizers.forEach((optimizer, name) => {
            if (optimizer.active) {
                try {
                    // 检查优化器是否还在正常工作
                    if (optimizer.instance.getStatus) {
                        const status = optimizer.instance.getStatus();
                        console.log(`📊 ${name}: ${JSON.stringify(status)}`);
                    }
                } catch (error) {
                    console.warn(`⚠️ 优化器 ${name} 状态检查失败:`, error);
                }
            }
        });
    }
    
    // 检测是否是复杂页面
    isComplexPage() {
        const complexPagePatterns = [
            '/reports/cargo_volume_dashboard',
            '/reports/',
            '/dashboard',
            '/outbound',
            '/inbound'
        ];

        const currentPath = window.location.pathname;
        return complexPagePatterns.some(pattern => currentPath.includes(pattern));
    }

    // 获取管理器状态
    getStatus() {
        return {
            totalOptimizers: this.optimizers.size,
            activeOptimizers: Array.from(this.optimizers.values()).filter(o => o.active).length,
            optimizers: Array.from(this.optimizers.entries()).map(([name, optimizer]) => ({
                name,
                priority: optimizer.priority,
                active: optimizer.active
            }))
        };
    }
    
    // 清理所有优化器
    cleanup() {
        console.log('🧹 清理所有性能优化器...');
        
        this.optimizers.forEach((optimizer, name) => {
            this.disableOptimizer(name);
        });
        
        this.optimizers.clear();
        console.log('✅ 所有优化器已清理');
    }
}

// 自动启动管理器
document.addEventListener('DOMContentLoaded', () => {
    if (!window.performanceOptimizerManager) {
        new PerformanceOptimizerManager();
    }
});

// 页面卸载时清理
window.addEventListener('beforeunload', () => {
    if (window.performanceOptimizerManager) {
        window.performanceOptimizerManager.cleanup();
    }
});

// 提供控制台命令
window.getOptimizerStatus = () => {
    if (window.performanceOptimizerManager) {
        return window.performanceOptimizerManager.getStatus();
    }
    return { error: '管理器未初始化' };
};

window.cleanupOptimizers = () => {
    if (window.performanceOptimizerManager) {
        window.performanceOptimizerManager.cleanup();
        return '✅ 优化器已清理';
    }
    return '❌ 管理器未初始化';
};
