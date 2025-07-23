/**
 * CSS优化监控器
 * 实时监控CSS优化效果，确保不会破坏页面显示
 */

class CSSOptimizationMonitor {
    constructor() {
        this.originalStyles = new Map();
        this.optimizationLog = [];
        this.isMonitoring = false;
        this.init();
    }

    init() {
        console.log('🎨 CSS优化监控器启动');
        this.startMonitoring();
        this.setupConsoleCommands();
    }

    startMonitoring() {
        this.isMonitoring = true;
        
        // 记录原始样式状态
        this.recordOriginalStyles();
        
        // 监控样式变化
        this.observeStyleChanges();
        
        // 定期检查样式完整性
        setInterval(() => {
            this.checkStyleIntegrity();
        }, 10000); // 每10秒检查一次
        
        console.log('✅ CSS优化监控已启动');
    }

    recordOriginalStyles() {
        // 记录所有CSS链接
        const cssLinks = document.querySelectorAll('link[rel="stylesheet"]');
        cssLinks.forEach((link, index) => {
            this.originalStyles.set(`css-link-${index}`, {
                href: link.href,
                media: link.media,
                disabled: link.disabled,
                element: link
            });
        });

        // 记录内联样式
        const styleElements = document.querySelectorAll('style');
        styleElements.forEach((style, index) => {
            this.originalStyles.set(`style-${index}`, {
                content: style.textContent,
                element: style
            });
        });

        console.log(`📝 已记录 ${this.originalStyles.size} 个原始样式`);
    }

    observeStyleChanges() {
        // 监控DOM变化
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            if (node.tagName === 'STYLE' || 
                                (node.tagName === 'LINK' && node.rel === 'stylesheet')) {
                                this.logOptimization('样式元素添加', node);
                            }
                        }
                    });
                }
                
                if (mutation.type === 'attributes' && 
                    (mutation.target.tagName === 'LINK' || mutation.target.tagName === 'STYLE')) {
                    this.logOptimization('样式属性修改', mutation.target, mutation.attributeName);
                }
            });
        });

        observer.observe(document.head, {
            childList: true,
            attributes: true,
            attributeFilter: ['media', 'disabled', 'importance']
        });
    }

    logOptimization(type, element, detail = '') {
        const log = {
            timestamp: new Date().toISOString(),
            type: type,
            element: element.tagName,
            detail: detail,
            safe: this.isOptimizationSafe(element)
        };

        this.optimizationLog.push(log);

        if (log.safe) {
            console.log(`✅ 安全优化: ${type}`, element);
        } else {
            console.warn(`⚠️ 可能有风险的优化: ${type}`, element);

            // 如果是重复的样式优化，建议移除
            if (type === '样式元素添加' && this.isDuplicateStyleOptimization(element)) {
                console.warn('🔄 检测到重复的样式优化，建议清理');
                this.suggestCleanup(element);
            }
        }
    }

    // 检测是否是重复的样式优化
    isDuplicateStyleOptimization(element) {
        if (element.tagName !== 'STYLE') return false;

        const optimizerAttributes = [
            'data-performance-optimizer',
            'data-safe-optimizer'
        ];

        // 检查是否有相同类型的优化器样式
        for (const attr of optimizerAttributes) {
            if (element.hasAttribute(attr)) {
                const existing = document.querySelectorAll(`style[${attr}]`);
                if (existing.length > 1) {
                    return true;
                }
            }
        }

        return false;
    }

    // 建议清理重复样式
    suggestCleanup(element) {
        console.log('💡 建议: 清理重复的性能优化样式');

        // 提供清理函数
        window.cleanupDuplicateStyles = () => {
            const duplicates = this.findDuplicateStyles();
            duplicates.forEach((duplicate, index) => {
                if (index > 0) { // 保留第一个，移除其他的
                    duplicate.remove();
                    console.log('🗑️ 移除重复样式:', duplicate);
                }
            });
        };
    }

    // 查找重复样式
    findDuplicateStyles() {
        const optimizerStyles = document.querySelectorAll('style[data-performance-optimizer], style[data-safe-optimizer]');
        const groups = {};

        optimizerStyles.forEach(style => {
            const key = style.getAttribute('data-performance-optimizer') || style.getAttribute('data-safe-optimizer');
            if (!groups[key]) groups[key] = [];
            groups[key].push(style);
        });

        return Object.values(groups).filter(group => group.length > 1).flat();
    }

    isOptimizationSafe(element) {
        // 检查优化是否安全
        if (element.tagName === 'STYLE') {
            // 检查是否是优化器添加的样式
            return element.hasAttribute('data-performance-optimizer') ||
                   element.hasAttribute('data-safe-optimizer');
        }
        
        if (element.tagName === 'LINK') {
            // 检查CSS链接是否仍然可访问
            return !element.disabled && element.href;
        }
        
        return true;
    }

    checkStyleIntegrity() {
        if (!this.isMonitoring) return;

        let issuesFound = 0;
        
        // 检查关键CSS是否仍然加载
        const criticalCSS = ['bootstrap', 'fontawesome', 'custom.css'];
        criticalCSS.forEach(css => {
            const found = Array.from(document.querySelectorAll('link[rel="stylesheet"]'))
                .some(link => link.href.includes(css) && !link.disabled);
            
            if (!found) {
                console.warn(`⚠️ 关键CSS可能丢失: ${css}`);
                issuesFound++;
            }
        });

        // 检查页面是否正常显示
        const body = document.body;
        const computedStyle = window.getComputedStyle(body);
        
        if (computedStyle.display === 'none' || computedStyle.visibility === 'hidden') {
            console.error('❌ 页面显示异常！');
            issuesFound++;
        }

        if (issuesFound === 0) {
            console.log('✅ 样式完整性检查通过');
        }

        return issuesFound === 0;
    }

    getOptimizationReport() {
        return {
            monitoring: this.isMonitoring,
            originalStylesCount: this.originalStyles.size,
            optimizationCount: this.optimizationLog.length,
            safeOptimizations: this.optimizationLog.filter(log => log.safe).length,
            riskyOptimizations: this.optimizationLog.filter(log => !log.safe).length,
            recentOptimizations: this.optimizationLog.slice(-10),
            styleIntegrityOK: this.checkStyleIntegrity()
        };
    }

    rollbackOptimizations() {
        console.log('🔄 开始回滚CSS优化...');
        
        // 移除优化器添加的样式
        const optimizerStyles = document.querySelectorAll('style[data-performance-optimizer], style[data-safe-optimizer]');
        optimizerStyles.forEach(style => {
            style.remove();
            console.log('🗑️ 移除优化样式:', style);
        });

        // 恢复原始CSS链接状态
        this.originalStyles.forEach((original, key) => {
            if (key.startsWith('css-link-') && original.element) {
                original.element.media = original.media;
                original.element.disabled = original.disabled;
            }
        });

        console.log('✅ CSS优化回滚完成');
    }

    setupConsoleCommands() {
        // 提供控制台命令
        window.cssMonitor = this;
        window.getCSSReport = () => this.getOptimizationReport();
        window.rollbackCSS = () => this.rollbackOptimizations();
        window.checkCSSIntegrity = () => this.checkStyleIntegrity();
    }
}

// 启动CSS优化监控器
if (!window.cssOptimizationMonitor) {
    window.cssOptimizationMonitor = new CSSOptimizationMonitor();
    
    console.log('🎨 CSS优化监控器已加载');
    console.log('💡 可用命令: getCSSReport(), rollbackCSS(), checkCSSIntegrity()');
}
