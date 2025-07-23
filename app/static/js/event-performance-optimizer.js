/**
 * 事件性能优化器
 * 解决点击事件响应慢的问题
 */

class EventPerformanceOptimizer {
    constructor() {
        this.eventQueue = [];
        this.isProcessing = false;
        this.performanceThreshold = 100; // 100ms阈值
        this.init();
    }

    init() {
        console.log('⚡ 事件性能优化器启动');
        this.optimizeClickEvents();
        this.setupEventThrottling();
        this.monitorEventPerformance();
    }

    optimizeClickEvents() {
        // 使用事件委托优化点击事件
        document.addEventListener('click', this.handleOptimizedClick.bind(this), {
            capture: true,
            passive: false
        });

        console.log('✅ 点击事件优化已启用');
    }

    handleOptimizedClick(event) {
        const startTime = performance.now();

        // 检查是否是需要优化的元素
        const target = event.target.closest('button, a, .btn, [data-toggle], [onclick]');
        if (!target) return;

        // 跳过模态框相关元素，避免干扰
        if (this.isModalRelatedElement(target)) {
            console.log('🎭 跳过模态框相关元素:', target);
            return;
        }

        // 防止重复点击
        if (target.dataset.processing === 'true') {
            event.preventDefault();
            event.stopPropagation();
            console.log('🚫 防止重复点击:', target);
            return;
        }

        // 标记为处理中
        target.dataset.processing = 'true';

        // 添加视觉反馈（但不禁用pointer events）
        target.style.opacity = '0.8';

        // 设置超时恢复（缩短时间，不禁用pointer events）
        setTimeout(() => {
            target.dataset.processing = 'false';
            target.style.opacity = '';
        }, 500);

        const endTime = performance.now();
        const duration = endTime - startTime;

        if (duration > this.performanceThreshold) {
            console.warn(`⚠️ 慢点击事件: ${duration.toFixed(2)}ms`, target);
        }
    }

    setupEventThrottling() {
        // 节流处理高频事件
        const throttledEvents = ['scroll', 'resize', 'mousemove'];
        
        throttledEvents.forEach(eventType => {
            let lastTime = 0;
            const throttleDelay = 16; // 60fps

            document.addEventListener(eventType, (event) => {
                const now = performance.now();
                if (now - lastTime >= throttleDelay) {
                    lastTime = now;
                    // 允许事件继续传播
                } else {
                    event.stopPropagation();
                }
            }, { capture: true, passive: true });
        });

        console.log('✅ 事件节流已启用');
    }

    // 检测是否是模态框相关元素
    isModalRelatedElement(element) {
        if (!element) return false;

        // 检查元素本身和父级是否包含模态框相关的类或属性
        const modalSelectors = [
            '.modal',
            '.modal-dialog',
            '.modal-content',
            '.modal-header',
            '.modal-body',
            '.modal-footer',
            '[data-bs-toggle="modal"]',
            '[data-bs-dismiss="modal"]',
            '.btn-close',
            '#inventoryModal',
            '#editWarehouseModal',
            '#viewWarehouseModal',
            '#createWarehouseModal'
        ];

        // 检查元素本身
        for (const selector of modalSelectors) {
            if (element.matches && element.matches(selector)) {
                return true;
            }
            if (element.closest && element.closest(selector)) {
                return true;
            }
        }

        // 检查是否在模态框内部
        const modalParent = element.closest('.modal');
        if (modalParent) {
            return true;
        }

        // 检查特定的onclick属性
        const onclickAttr = element.getAttribute('onclick');
        if (onclickAttr && (
            onclickAttr.includes('Modal') ||
            onclickAttr.includes('modal') ||
            onclickAttr.includes('showInventorySelector') ||
            onclickAttr.includes('editWarehouse') ||
            onclickAttr.includes('viewWarehouse')
        )) {
            return true;
        }

        return false;
    }

    monitorEventPerformance() {
        // 监控事件性能
        const originalAddEventListener = EventTarget.prototype.addEventListener;
        const self = this;

        EventTarget.prototype.addEventListener = function(type, listener, options) {
            const wrappedListener = function(event) {
                const startTime = performance.now();
                
                try {
                    const result = listener.call(this, event);
                    
                    const endTime = performance.now();
                    const duration = endTime - startTime;
                    
                    if (duration > self.performanceThreshold) {
                        console.warn(`⚠️ 慢事件处理 (${type}): ${duration.toFixed(2)}ms`, this);
                    }
                    
                    return result;
                } catch (error) {
                    console.error('❌ 事件处理错误:', error);
                    throw error;
                }
            };

            return originalAddEventListener.call(this, type, wrappedListener, options);
        };

        console.log('✅ 事件性能监控已启用');
    }

    // 批量处理事件
    batchProcessEvents(events) {
        if (this.isProcessing) return;
        
        this.isProcessing = true;
        
        requestAnimationFrame(() => {
            events.forEach(event => {
                try {
                    event.handler.call(event.target, event.originalEvent);
                } catch (error) {
                    console.error('批量事件处理错误:', error);
                }
            });
            
            this.isProcessing = false;
        });
    }

    // 获取性能报告
    getPerformanceReport() {
        return {
            optimizerActive: true,
            eventsOptimized: true,
            throttlingEnabled: true,
            performanceThreshold: this.performanceThreshold,
            timestamp: new Date().toISOString()
        };
    }
}

// 启动事件性能优化器
if (!window.eventPerformanceOptimizer) {
    window.eventPerformanceOptimizer = new EventPerformanceOptimizer();
    
    // 提供控制台接口
    window.getEventPerformanceReport = () => window.eventPerformanceOptimizer.getPerformanceReport();
    
    console.log('⚡ 事件性能优化器已加载');
    console.log('💡 可用命令: getEventPerformanceReport()');
}
